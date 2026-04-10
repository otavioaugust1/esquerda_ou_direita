"""
Funções utilitárias: normalização de texto, filtros e busca na web.
"""

import re
from urllib.parse import urlparse

import requests

from .dados import TIMEOUT

try:
    from ddgs import DDGS

    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS

        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False


def normalizar_texto(texto):
    """Remove acentos e normaliza."""
    texto = texto.lower()
    acentos = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'õ': 'o', 'ô': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c',
    }
    for antigo, novo in acentos.items():
        texto = texto.replace(antigo, novo)
    return texto


def filtrar_resultados_username(posts, username):
    """
    Filtra resultados para garantir que pertencem ao username EXATO.
    - Se há @menções ou URLs de rede social no resultado, exige match exato.
    - Se não há menções, exige que o username apareça no texto ou URL.
    """
    username_lower = username.lower()
    filtrados = []

    for post in posts:
        texto_lower = post.get('texto', '').lower()
        url_lower = post.get('url', '').lower()
        combinado = texto_lower + ' ' + url_lower

        mencoes_at = re.findall(r'@([a-zA-Z0-9_.]+)', combinado)
        mencoes_url = re.findall(
            r'(?:twitter\.com|x\.com|instagram\.com|facebook\.com|nitter\.[a-z.]+)/([a-zA-Z0-9_.]+)',
            combinado,
        )

        todas_mencoes = mencoes_at + mencoes_url

        if todas_mencoes:
            tem_exato = False
            for mencao in todas_mencoes:
                mencao = mencao.rstrip('/').lower()
                if mencao == username_lower:
                    tem_exato = True
                    break
            if not tem_exato:
                continue
        else:
            if username_lower not in combinado:
                continue

        filtrados.append(post)

    return filtrados


def filtrar_por_dominio(posts, dominios_aceitos):
    """
    Filtra posts para manter apenas URLs de domínios aceitos.
    Posts sem URL são descartados.
    """
    filtrados = []
    for post in posts:
        url = post.get('url', '').lower()
        if any(d in url for d in dominios_aceitos):
            filtrados.append(post)
    return filtrados


def buscar_web(query, max_results=15):
    """Busca web usando ddgs (lib) com fallback para Bing.
    Filtra automaticamente resultados estrangeiros/irrelevantes.
    """
    posts = []

    _SCRIPT_ESTRANGEIRO = re.compile(
        r'[\u0400-\u04FF\u0500-\u052F'
        r'\u4E00-\u9FFF\u3400-\u4DBF'
        r'\u3040-\u309F\u30A0-\u30FF'
        r'\uAC00-\uD7AF'
        r'\u0600-\u06FF'
        r'\u0E00-\u0E7F'
        r']',
    )

    _TLDS_BLOQUEADOS = (
        '.ru', '.cn', '.jp', '.kr', '.kz', '.ua', '.by', '.su',
        '.ir', '.th', '.vn', '.in', '.pk', '.sa', '.ae',
    )

    _DOMINIOS_BLOQUEADOS = (
        'vkvideo.ru', 'vk.com', 'vk.ru', 'ok.ru', 'mail.ru',
        'weibo.com', 'baidu.com', 'yandex.', 'qq.com',
        'naver.com', 'daum.net', 'rakuten.',
        'tiktok.com',
    )

    def _resultado_relevante(href, texto):
        href_lower = href.lower()
        try:
            dominio = urlparse(href_lower).hostname or ''
        except Exception:
            dominio = ''
        if any(dominio.endswith(tld) for tld in _TLDS_BLOQUEADOS):
            return False
        if any(d in href_lower for d in _DOMINIOS_BLOQUEADOS):
            return False
        if _SCRIPT_ESTRANGEIRO.search(texto):
            return False
        return True

    if HAS_DDGS:
        try:
            ddgs = DDGS()
            results = ddgs.text(query, region='br-pt', max_results=max_results)
            for r in results:
                titulo = r.get('title', '')
                body = r.get('body', '')
                href = r.get('href', '')
                texto = f'{titulo}. {body}'
                if len(texto) <= 20:
                    continue
                if not _resultado_relevante(href, texto):
                    continue
                posts.append({'texto': texto, 'fonte': 'Busca Web', 'url': href})
            return posts
        except Exception:
            pass

    # Fallback: Bing
    try:
        url = 'https://www.bing.com/search'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        params = {'q': query, 'setlang': 'pt-BR', 'cc': 'BR'}
        resp = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)

        if resp.status_code == 200:
            results = re.findall(
                r'<h2><a[^>]*href="([^"]*)"[^>]*>(.*?)</a></h2>.*?<p[^>]*>(.*?)</p>',
                resp.text,
                re.DOTALL,
            )
            for href, titulo, snippet in results[:max_results]:
                titulo = re.sub(r'<[^>]+>', '', titulo).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                texto = f'{titulo}. {snippet}'
                if len(texto) <= 20:
                    continue
                if not _resultado_relevante(href, texto):
                    continue
                posts.append({'texto': texto, 'fonte': 'Busca Web', 'url': href})
    except Exception:
        pass

    return posts


def buscar_noticias(nome):
    """Busca notícias via Google News RSS."""
    posts = []
    try:
        url = 'https://news.google.com/rss/search'
        params = {'q': nome, 'hl': 'pt-BR', 'gl': 'BR', 'ceid': 'BR:pt-419'}
        resp = requests.get(url, params=params, timeout=TIMEOUT)

        if resp.status_code == 200:
            titulos = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
            if not titulos:
                titulos = re.findall(r'<title>(.*?)</title>', resp.text)
            for titulo in titulos[1:30]:
                titulo = re.sub(r'<[^>]+>', '', titulo).strip()
                if len(titulo) > 15:
                    posts.append({
                        'texto': titulo,
                        'fonte': 'Google News',
                        'url': 'https://news.google.com/',
                    })
    except Exception:
        pass
    return posts


def buscar_wikipedia(nome):
    """Busca informações na Wikipédia PT."""
    posts = []
    try:
        url = 'https://pt.wikipedia.org/w/api.php'
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': nome,
            'format': 'json',
            'utf8': 1,
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT)

        if resp.status_code == 200:
            resultados = resp.json().get('query', {}).get('search', [])
            if resultados:
                titulo_pagina = resultados[0]['title']
                params2 = {
                    'action': 'query',
                    'prop': 'extracts',
                    'exintro': True,
                    'explaintext': True,
                    'titles': titulo_pagina,
                    'format': 'json',
                }
                resp2 = requests.get(url, params=params2, timeout=TIMEOUT)

                if resp2.status_code == 200:
                    pages = resp2.json().get('query', {}).get('pages', {})
                    for _, page_data in pages.items():
                        extract = page_data.get('extract', '')
                        if extract and len(extract) > 50:
                            for paragrafo in extract.split('\n')[:5]:
                                if len(paragrafo) > 30:
                                    posts.append({
                                        'texto': paragrafo,
                                        'fonte': 'Wikipédia',
                                        'url': f"https://pt.wikipedia.org/wiki/{titulo_pagina.replace(' ', '_')}",
                                    })
    except Exception:
        pass
    return posts


# ---------------------------------------------------------------------------
# Verificação de existência de perfil em cada plataforma
# ---------------------------------------------------------------------------

_HEADERS_BROWSER = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
}


def verificar_perfil_twitter(username):
    """Verifica se o perfil existe no X/Twitter. Retorna True/False."""
    # Tentar Nitter/xcancel primeiro (mais confiável sem JS)
    nitter_instances = ['xcancel.com', 'nitter.poast.org', 'nitter.privacydev.net']
    for inst in nitter_instances:
        try:
            resp = requests.get(
                f'https://{inst}/{username}',
                headers=_HEADERS_BROWSER, timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                text_lower = resp.text.lower()
                if 'user not found' in text_lower or 'not found' in text_lower[:500]:
                    return False
                if username.lower() in text_lower:
                    return True
            elif resp.status_code in (404,):
                return False
        except Exception:
            continue

    # Fallback: checar x.com direto (pode bloquear)
    try:
        resp = requests.get(
            f'https://x.com/{username}',
            headers=_HEADERS_BROWSER, timeout=TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code in (404, 403):
            return False
        if resp.status_code == 200:
            text_lower = resp.text.lower()
            if any(ind in text_lower for ind in [
                'this account doesn', 'essa conta não',
                'account suspended', 'conta suspensa',
            ]):
                return False
            return True
    except Exception:
        pass

    # Não conseguiu confirmar — assume que NÃO existe para evitar falso positivo
    return False


def verificar_perfil_instagram(username):
    """Verifica se o perfil existe no Instagram. Retorna (existe, privado, html)."""
    try:
        url = f'https://www.instagram.com/{username}/'
        resp = requests.get(
            url, headers=_HEADERS_BROWSER, timeout=TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code == 200:
            text = resp.text
            if 'Page Not Found' in text or '"HttpErrorPage"' in text:
                return False, False, ''
            privado = '"is_private":true' in text
            return True, privado, text
        return False, False, ''
    except Exception:
        return False, False, ''


def verificar_perfil_facebook(username):
    """Verifica se a página/perfil existe no Facebook. Retorna (existe, html)."""
    try:
        url = f'https://www.facebook.com/{username}'
        resp = requests.get(
            url, headers=_HEADERS_BROWSER, timeout=TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code == 200:
            text = resp.text
            if '/login' in resp.url or 'login_form' in text[:2000]:
                return False, ''
            if 'page_not_found' in text.lower() or 'this content isn' in text.lower():
                return False, ''
            return True, text
        return False, ''
    except Exception:
        return False, ''
