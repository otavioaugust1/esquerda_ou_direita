"""
MÓDULO DE ANÁLISE POLÍTICA — POR PLATAFORMA
Coleta dados públicos de redes sociais e classifica orientação política.
Analisa cada plataforma (Twitter/X, Instagram, Facebook) separadamente.
Fontes: Twitter/X (API v2), Web Scraping, Google News, Wikipédia, DuckDuckGo
"""

import json
import os
import re
from collections import Counter
from urllib.parse import quote_plus

import requests

try:
    from ddgs import DDGS

    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS

        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False

# =========================
# CONFIGURAÇÕES
# =========================

TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
TIMEOUT = 12

# =========================
# BANCO DE FIGURAS POLÍTICAS CONHECIDAS
# score: -2 = esquerda forte, -1 = centro-esquerda,
#         0 = centro, 1 = centro-direita, 2 = direita forte
# =========================

FIGURAS_POLITICAS = {
    # ── ESQUERDA FORTE (-2) ──
    'luaborges': ('Lua Borges', -2),
    'lulaoficial': ('Lula', -2),
    'labordes': ('Lula Instagram', -2),
    'dilmabr': ('Dilma Rousseff', -2),
    'andrejanonesadv': ('André Janones', -2),
    'guilhermeboulos': ('Guilherme Boulos', -2),
    'guilherme.boulos': ('Guilherme Boulos', -2),
    'gleaborges': ('Gleisi Hoffmann', -2),
    'gleaborgs': ('Gleisi Hoffmann', -2),
    'gleisihoffmann': ('Gleisi Hoffmann', -2),
    'fernandohaddad': ('Fernando Haddad', -2),
    'jandirafeghali': ('Jandira Feghali', -2),
    'marcelofreixo': ('Marcelo Freixo', -2),
    'samiabomfim': ('Sâmia Bomfim', -2),
    'pt_brasil': ('PT', -2),
    'pabordes': ('PT', -2),
    'pcdoboficial': ('PCdoB', -2),
    'pabordes45': ('PSOL', -2),
    'psabordes': ('PSOL', -2),
    'gduvivier': ('Gregório Duvivier', -2),
    'gregorioduvivier': ('Gregório Duvivier', -2),
    'jeanwyllys_real': ('Jean Wyllys', -2),
    'brenoaltman': ('Breno Altman', -2),
    'jonesmanoel': ('Jones Manoel', -2),
    'sabrinafernandes': ('Sabrina Fernandes', -2),
    'tempodecerejas': ('Sabrina Fernandes', -2),
    'brasil247': ('Brasil 247', -2),
    'dcm_online': ('DCM Online', -2),
    'midia_ninja': ('Mídia NINJA', -2),
    'midianinja': ('Mídia NINJA', -2),
    'tv247': ('TV 247', -2),
    'conversaafiada': ('Conversa Afiada', -2),
    'foraborges': ('Fórum', -2),
    'operamundi': ('Opera Mundi', -2),
    # ── CENTRO-ESQUERDA (-1) ──
    'ciaborges': ('Ciro Gomes', -1),
    'cirogomes': ('Ciro Gomes', -1),
    'marinasilvabr': ('Marina Silva', -1),
    'marinasilva': ('Marina Silva', -1),
    'flaviodino': ('Flávio Dino', -1),
    'tabataamaralsp': ('Tabata Amaral', -1),
    'reinaldoazevedo': ('Reinaldo Azevedo', -1),
    'luisnassif': ('Luís Nassif', -1),
    'leonardosakamoto': ('Leonardo Sakamoto', -1),
    'jucakfouri': ('Juca Kfouri', -1),
    'cartacapital': ('Carta Capital', -1),
    'theintercept_br': ('The Intercept Brasil', -1),
    'theinterceptbr': ('The Intercept Brasil', -1),
    # ── CENTRO (0) ──
    'folha': ('Folha de S.Paulo', 0),
    'folhadespaulo': ('Folha de S.Paulo', 0),
    'estadao': ('Estadão', 0),
    'oglobo_rio': ('O Globo', 0),
    'oglobo': ('O Globo', 0),
    'g1': ('G1', 0),
    'portalg1': ('G1', 0),
    'uaborges': ('UOL', 0),
    'uol': ('UOL', 0),
    'uolnoticias': ('UOL Notícias', 0),
    'bbcbrasil': ('BBC Brasil', 0),
    'cnn_brasil': ('CNN Brasil', 0),
    'cnnbrasil': ('CNN Brasil', 0),
    'bandnewsfm': ('BandNews', 0),
    'sabordes': ('SBT', 0),
    'recordtv': ('Record', 0),
    'jornalnacional': ('Jornal Nacional', 0),
    # ── CENTRO-DIREITA (1) ──
    'tarcisiogdf': ('Tarcísio de Freitas', 1),
    'sergiomoro': ('Sérgio Moro', 1),
    'romeuzema': ('Romeu Zema', 1),
    'kimkataguiri': ('Kim Kataguiri', 1),
    'marcelvanhattem': ('Marcel van Hattem', 1),
    'partidonovo30': ('Partido NOVO', 1),
    'oantagonista': ('O Antagonista', 1),
    'gazetadopovo': ('Gazeta do Povo', 1),
    'jovempannews': ('Jovem Pan News', 1),
    'jovempan': ('Jovem Pan', 1),
    'alexandregarcia': ('Alexandre Garcia', 1),
    'leandronarloch': ('Leandro Narloch', 1),
    'marcopontes': ('Marcos Pontes', 1),
    'osmarterra': ('Osmar Terra', 1),
    # ── DIREITA FORTE (2) ──
    'jabordes_': ('Jair Bolsonaro', 2),
    'jairbolsonaro': ('Jair Bolsonaro', 2),
    'bolsonaro': ('Jair Bolsonaro', 2),
    'flaviobolsonaro': ('Flávio Bolsonaro', 2),
    'carlosbolsonaro': ('Carlos Bolsonaro', 2),
    'eduardobolsonaro': ('Eduardo Bolsonaro', 2),
    'edubolsonaro': ('Eduardo Bolsonaro', 2),
    'michellebolsonaro': ('Michelle Bolsonaro', 2),
    'damaresalves': ('Damares Alves', 2),
    'nikolasferreira': ('Nikolas Ferreira', 2),
    'carlazambelli': ('Carla Zambelli', 2),
    'pl_brasil': ('PL', 2),
    'rodrigoconstantino': ('Rodrigo Constantino', 2),
    'allandossantos': ('Allan dos Santos', 2),
    'bernardopkuster': ('Bernardo P. Küster', 2),
    'gustavogayer': ('Gustavo Gayer', 2),
    'pablomarcal': ('Pablo Marçal', 2),
    'pablo_marcal': ('Pablo Marçal', 2),
    'revistaoeste': ('Revista Oeste', 2),
    'brasilparalelo': ('Brasil Paralelo', 2),
    'bparalelo': ('Brasil Paralelo', 2),
    'tercalivre': ('Terça Livre', 2),
    'sensoincomum': ('Senso Incomum', 2),
    'conexaopolitica': ('Conexão Política', 2),
}

# Nomes para busca textual em notícias/bio
NOMES_ESQUERDA = {
    'lula',
    'dilma',
    'haddad',
    'boulos',
    'gleisi',
    'janones',
    'jandira',
    'feghali',
    'freixo',
    'dino',
    'marina silva',
    'ciro gomes',
    'samia',
    'bomfim',
    'jean wyllys',
    'psol',
    'pcdob',
    'jones manoel',
    'sabrina fernandes',
    'gregorio',
    'duvivier',
    'sakamoto',
    'nassif',
    'kfouri',
    'brasil 247',
    'dcm',
    'carta capital',
    'intercept',
    'ninja',
    'opera mundi',
    'altman',
}

NOMES_DIREITA = {
    'bolsonaro',
    'moro',
    'zema',
    'tarcisio',
    'nikolas',
    'zambelli',
    'damares',
    'eduardo bolsonaro',
    'carlos bolsonaro',
    'flavio bolsonaro',
    'kim kataguiri',
    'van hattem',
    'constantino',
    'narloch',
    'pablo marcal',
    'gayer',
    'allan santos',
    'kuster',
    'olavo',
    'antagonista',
    'gazeta do povo',
    'oeste',
    'jovem pan',
    'brasil paralelo',
    'senso incomum',
}

PALAVRAS_ESQUERDA = {
    'democracia',
    'democratico',
    'direitos',
    'humanos',
    'justica',
    'social',
    'igualdade',
    'trabalhador',
    'trabalhadores',
    'sus',
    'saude',
    'publica',
    'educacao',
    'feminismo',
    'feminista',
    'lgbt',
    'lgbtqia',
    'diversidade',
    'inclusao',
    'ambiente',
    'amazonia',
    'indigena',
    'quilombola',
    'reforma',
    'agraria',
    'pt',
    'psol',
    'pcdob',
    'lula',
    'dilma',
    'boulos',
    'socialismo',
    'socialista',
    'progressista',
    'coletivo',
    'popular',
    'povo',
    'antifascismo',
    'antifascista',
    'resistencia',
    'redistribuicao',
    'minorias',
    'oprimidos',
    'intervencao',
    'regulacao',
    'soberania',
    'haddad',
    'janones',
    'freixo',
    'duvivier',
    'sakamoto',
}

PALAVRAS_DIREITA = {
    'liberdade',
    'economica',
    'livre',
    'mercado',
    'capitalismo',
    'empreendedor',
    'empreendedorismo',
    'privatizacao',
    'privatizar',
    'meritocracia',
    'imposto',
    'impostos',
    'reducao',
    'familia',
    'tradicional',
    'cristaos',
    'cristao',
    'conservador',
    'conservadorismo',
    'bolsonaro',
    'direita',
    'corrupcao',
    'petismo',
    'patriota',
    'patriotismo',
    'armamento',
    'armas',
    'seguranca',
    'ordem',
    'militar',
    'agronegocio',
    'agro',
    'liberal',
    'liberalismo',
    'propriedade',
    'privada',
    'anticomunismo',
    'anticomunista',
    'comunismo',
    'doutrinacao',
    'ideologia',
    'genero',
    'valores',
    'moral',
    'nacao',
    'nacionalismo',
    'moro',
    'nikolas',
    'zambelli',
    'marcal',
    'gayer',
}


# =========================
# UTILIDADES
# =========================


def normalizar_texto(texto):
    """Remove acentos e normaliza."""
    texto = texto.lower()
    acentos = {
        'á': 'a',
        'à': 'a',
        'ã': 'a',
        'â': 'a',
        'é': 'e',
        'ê': 'e',
        'í': 'i',
        'ó': 'o',
        'õ': 'o',
        'ô': 'o',
        'ú': 'u',
        'ü': 'u',
        'ç': 'c',
    }
    for antigo, novo in acentos.items():
        texto = texto.replace(antigo, novo)
    return texto


def buscar_web(query, max_results=15):
    """Busca web usando ddgs (lib) com fallback para Bing."""
    posts = []

    if HAS_DDGS:
        try:
            ddgs = DDGS()
            results = ddgs.text(query, region='br-pt', max_results=max_results)
            for r in results:
                titulo = r.get('title', '')
                body = r.get('body', '')
                texto = f'{titulo}. {body}'
                if len(texto) > 20:
                    posts.append(
                        {
                            'texto': texto,
                            'fonte': 'Busca Web',
                            'url': r.get('href', ''),
                        }
                    )
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
        resp = requests.get(
            url, headers=headers, params=params, timeout=TIMEOUT
        )

        if resp.status_code == 200:
            results = re.findall(
                r'<h2><a[^>]*>(.*?)</a></h2>.*?<p[^>]*>(.*?)</p>',
                resp.text,
                re.DOTALL,
            )
            for titulo, snippet in results[:max_results]:
                titulo = re.sub(r'<[^>]+>', '', titulo).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                texto = f'{titulo}. {snippet}'
                if len(texto) > 20:
                    posts.append(
                        {'texto': texto, 'fonte': 'Busca Web', 'url': ''}
                    )
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
            titulos = re.findall(
                r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text
            )
            if not titulos:
                titulos = re.findall(r'<title>(.*?)</title>', resp.text)
            for titulo in titulos[1:30]:
                titulo = re.sub(r'<[^>]+>', '', titulo).strip()
                if len(titulo) > 15:
                    posts.append(
                        {
                            'texto': titulo,
                            'fonte': 'Google News',
                            'url': 'https://news.google.com/',
                        }
                    )
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
                    for page_id, page_data in pages.items():
                        extract = page_data.get('extract', '')
                        if extract and len(extract) > 50:
                            for paragrafo in extract.split('\n')[:5]:
                                if len(paragrafo) > 30:
                                    posts.append(
                                        {
                                            'texto': paragrafo,
                                            'fonte': 'Wikipédia',
                                            'url': f"https://pt.wikipedia.org/wiki/{titulo_pagina.replace(' ', '_')}",
                                        }
                                    )
    except Exception:
        pass
    return posts


# =========================
# ANÁLISE DE TEXTO
# =========================


def analisar_por_palavras(posts):
    """Analisa posts por palavras-chave e nomes conhecidos."""
    total_esq = 0
    total_dir = 0
    palavras_esq = []
    palavras_dir = []

    for post in posts:
        texto_norm = normalizar_texto(post.get('texto', ''))
        palavras = re.findall(r'\b\w+\b', texto_norm)

        for palavra in palavras:
            if palavra in PALAVRAS_ESQUERDA:
                total_esq += 1
                palavras_esq.append(palavra)
            elif palavra in PALAVRAS_DIREITA:
                total_dir += 1
                palavras_dir.append(palavra)

        for nome in NOMES_ESQUERDA:
            if nome in texto_norm:
                total_esq += 2
                palavras_esq.append(nome.strip())
        for nome in NOMES_DIREITA:
            if nome in texto_norm:
                total_dir += 2
                palavras_dir.append(nome.strip())

    return total_esq, total_dir, palavras_esq, palavras_dir


def analisar_seguidores(seguindo_politicos):
    """Analisa figuras políticas seguidas (peso forte)."""
    score_esq = 0
    score_dir = 0
    figuras_esq = []
    figuras_dir = []

    for fig in seguindo_politicos:
        score = fig['score']
        nome = fig['nome']
        if score < 0:
            score_esq += abs(score) * 3
            figuras_esq.append(nome)
        elif score > 0:
            score_dir += score * 3
            figuras_dir.append(nome)

    return score_esq, score_dir, figuras_esq, figuras_dir


def classificar(pct_esq, pct_dir, total_pontos):
    """Gera classificação, descrição, confiança e cor."""
    if total_pontos < 3:
        return (
            'INCONCLUSIVO',
            'Dados insuficientes para esta plataforma',
            'NENHUMA',
            '#888888',
        )

    if total_pontos < 5:
        confianca = 'MUITO BAIXA'
    elif total_pontos < 15:
        confianca = 'BAIXA'
    elif total_pontos < 30:
        confianca = 'MÉDIA'
    else:
        confianca = 'ALTA'

    diff = abs(pct_esq - pct_dir)

    if diff < 12:
        return (
            'CENTRO',
            'Posicionamento equilibrado entre esquerda e direita',
            confianca,
            '#f59e0b',
        )
    elif diff < 30:
        if pct_esq > pct_dir:
            return (
                'CENTRO-ESQUERDA',
                'Tendência moderada para a esquerda',
                confianca,
                '#f97316',
            )
        else:
            return (
                'CENTRO-DIREITA',
                'Tendência moderada para a direita',
                confianca,
                '#3b82f6',
            )
    else:
        if pct_esq > pct_dir:
            return (
                'ESQUERDA',
                'Posicionamento claramente à esquerda',
                confianca,
                '#ef4444',
            )
        else:
            return (
                'DIREITA',
                'Posicionamento claramente à direita',
                confianca,
                '#2563eb',
            )


def montar_resultado_plataforma(posts, seguindo_politicos=None):
    """Analisa uma lista de posts e retorna resultado de uma plataforma."""
    if seguindo_politicos is None:
        seguindo_politicos = []

    (
        pts_esq_texto,
        pts_dir_texto,
        palavras_esq,
        palavras_dir,
    ) = analisar_por_palavras(posts)
    pts_esq_seg, pts_dir_seg, figuras_esq, figuras_dir = analisar_seguidores(
        seguindo_politicos
    )

    total_esq = pts_esq_texto + pts_esq_seg
    total_dir = pts_dir_texto + pts_dir_seg
    total = total_esq + total_dir

    if total == 0:
        return {
            'total_posts': len(posts),
            'classificacao': 'INCONCLUSIVO',
            'descricao': 'Dados insuficientes para esta plataforma',
            'esquerda_pct': 0,
            'direita_pct': 0,
            'confianca': 'NENHUMA',
            'cor': '#888888',
            'pontos_esq': 0,
            'pontos_dir': 0,
            'top_palavras_esq': [],
            'top_palavras_dir': [],
            'seguindo_politicos': seguindo_politicos,
            'figuras_esq': list(set(figuras_esq))[:10],
            'figuras_dir': list(set(figuras_dir))[:10],
            'exemplos': [
                {'texto': p['texto'][:200], 'fonte': p['fonte']}
                for p in posts[:8]
            ],
        }

    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    classe, descricao, confianca, cor = classificar(pct_esq, pct_dir, total)

    return {
        'total_posts': len(posts),
        'classificacao': classe,
        'descricao': descricao,
        'esquerda_pct': round(pct_esq, 1),
        'direita_pct': round(pct_dir, 1),
        'confianca': confianca,
        'cor': cor,
        'pontos_esq': total_esq,
        'pontos_dir': total_dir,
        'top_palavras_esq': Counter(palavras_esq).most_common(10),
        'top_palavras_dir': Counter(palavras_dir).most_common(10),
        'seguindo_politicos': seguindo_politicos,
        'figuras_esq': list(set(figuras_esq))[:10],
        'figuras_dir': list(set(figuras_dir))[:10],
        'exemplos': [
            {'texto': p['texto'][:200], 'fonte': p['fonte']} for p in posts[:8]
        ],
    }


# =====================================================
# COLETA POR PLATAFORMA
# =====================================================


def coletar_twitter(username, nome_completo):
    """Coleta dados do Twitter/X: tweets, seguidores, busca web."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}

    # 1) API oficial
    if TWITTER_BEARER_TOKEN:
        headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}

        # Tweets
        logs.append({'fonte': 'X — Tweets (API)', 'status': 'buscando'})
        try:
            url_user = (
                f'https://api.twitter.com/2/users/by/username/{username}'
            )
            resp = requests.get(url_user, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 200 and 'data' in resp.json():
                user_id = resp.json()['data']['id']

                url_tweets = (
                    f'https://api.twitter.com/2/users/{user_id}/tweets'
                )
                params = {
                    'max_results': 100,
                    'tweet.fields': 'created_at,text,public_metrics',
                }
                resp_tw = requests.get(
                    url_tweets, headers=headers, params=params, timeout=TIMEOUT
                )

                if resp_tw.status_code == 200:
                    for tweet in resp_tw.json().get('data', []):
                        texto = tweet.get('text', '')
                        if len(texto) > 15:
                            posts.append(
                                {
                                    'texto': texto,
                                    'fonte': 'X — Tweet',
                                    'url': f"https://x.com/{username}/status/{tweet.get('id')}",
                                }
                            )
                    fontes['X — Tweets'] = len(posts)
                    logs.append(
                        {
                            'fonte': 'X — Tweets (API)',
                            'status': 'ok',
                            'qtd': len(posts),
                        }
                    )
                else:
                    logs.append(
                        {
                            'fonte': 'X — Tweets (API)',
                            'status': 'aviso',
                            'msg': f'HTTP {resp_tw.status_code}',
                        }
                    )

                # Seguindo
                logs.append(
                    {'fonte': 'X — Seguindo (API)', 'status': 'buscando'}
                )
                url_following = (
                    f'https://api.twitter.com/2/users/{user_id}/following'
                )
                all_following = []
                next_token = None
                for _ in range(3):
                    p = {
                        'max_results': 100,
                        'user.fields': 'name,username,description',
                    }
                    if next_token:
                        p['pagination_token'] = next_token
                    resp_f = requests.get(
                        url_following,
                        headers=headers,
                        params=p,
                        timeout=TIMEOUT,
                    )
                    if resp_f.status_code != 200:
                        break
                    data = resp_f.json()
                    all_following.extend(data.get('data', []))
                    next_token = data.get('meta', {}).get('next_token')
                    if not next_token:
                        break

                for user in all_following:
                    uname = user.get('username', '').lower()
                    desc = user.get('description', '')
                    if uname in FIGURAS_POLITICAS:
                        nome_fig, score = FIGURAS_POLITICAS[uname]
                        seguindo_politicos.append(
                            {
                                'username': uname,
                                'nome': nome_fig,
                                'score': score,
                                'descricao': desc[:120] if desc else '',
                            }
                        )
                    if desc and len(desc) > 10:
                        posts.append(
                            {
                                'texto': f"{user.get('name', '')}: {desc}",
                                'fonte': 'X — Bio seguido',
                                'url': f'https://x.com/{uname}',
                            }
                        )

                if seguindo_politicos:
                    fontes['X — Figuras seguidas'] = len(seguindo_politicos)
                    logs.append(
                        {
                            'fonte': 'X — Seguindo (API)',
                            'status': 'ok',
                            'qtd': len(seguindo_politicos),
                            'msg': f'{len(seguindo_politicos)} figuras políticas',
                        }
                    )
                else:
                    logs.append(
                        {
                            'fonte': 'X — Seguindo (API)',
                            'status': 'aviso',
                            'msg': 'Nenhuma figura política identificada',
                        }
                    )
            else:
                logs.append(
                    {
                        'fonte': 'X — Tweets (API)',
                        'status': 'aviso',
                        'msg': 'Usuário não encontrado na API',
                    }
                )

        except Exception as e:
            logs.append(
                {'fonte': 'X — Tweets (API)', 'status': 'erro', 'msg': str(e)}
            )

    else:
        # Sem API — Nitter
        logs.append({'fonte': 'X — Nitter', 'status': 'buscando'})
        instancias = [
            'nitter.poast.org',
            'nitter.privacydev.net',
            'nitter.net',
            'nitter.cz',
        ]
        for instancia in instancias:
            try:
                url = f'https://{instancia}/{username}'
                h = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=h, timeout=TIMEOUT)
                if response.status_code == 200:
                    tweets = re.findall(
                        r'class="tweet-content[^"]*"[^>]*>([^<]+)',
                        response.text,
                    )
                    for tweet in tweets:
                        texto = re.sub(r'<[^>]+>', '', tweet).strip()
                        if len(texto) > 15:
                            posts.append(
                                {
                                    'texto': texto,
                                    'fonte': 'X — Nitter',
                                    'url': f'https://x.com/{username}',
                                }
                            )
                    if posts:
                        fontes['X — Nitter'] = len(posts)
                        logs.append(
                            {
                                'fonte': 'X — Nitter',
                                'status': 'ok',
                                'qtd': len(posts),
                            }
                        )
                        break
            except Exception:
                continue
        if not posts:
            logs.append(
                {
                    'fonte': 'X — Nitter',
                    'status': 'aviso',
                    'msg': 'Nitter indisponível',
                }
            )

    # 2) Busca web específica do Twitter
    logs.append({'fonte': 'X — Busca Web', 'status': 'buscando'})
    queries = [
        f'site:x.com OR site:twitter.com @{username} política',
        f'@{username} twitter opinião política',
    ]
    posts_web = []
    for q in queries:
        posts_web.extend(buscar_web(q, max_results=8))

    for p in posts_web:
        p['fonte'] = 'X — Busca Web'
    posts.extend(posts_web)
    if posts_web:
        fontes['X — Busca Web'] = len(posts_web)
        logs.append(
            {'fonte': 'X — Busca Web', 'status': 'ok', 'qtd': len(posts_web)}
        )
    else:
        logs.append(
            {
                'fonte': 'X — Busca Web',
                'status': 'aviso',
                'msg': 'Nenhum resultado',
            }
        )

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    return resultado


def coletar_instagram(username, nome_completo):
    """Coleta dados do Instagram: busca web por perfil, curtidas, seguidos."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}

    # 1) Busca web por perfil Instagram
    logs.append({'fonte': 'Instagram — Perfil Web', 'status': 'buscando'})
    queries = [
        f'site:instagram.com "{username}" política',
        f'instagram @{username} curtidas seguindo política',
        f'"{nome_completo}" instagram posição política',
    ]
    for q in queries:
        resultados = buscar_web(q, max_results=8)
        for r in resultados:
            r['fonte'] = 'Instagram — Busca Web'
        posts.extend(resultados)

    if posts:
        fontes['Instagram — Busca Web'] = len(posts)
        logs.append(
            {
                'fonte': 'Instagram — Perfil Web',
                'status': 'ok',
                'qtd': len(posts),
            }
        )
    else:
        logs.append(
            {
                'fonte': 'Instagram — Perfil Web',
                'status': 'aviso',
                'msg': 'Nenhum conteúdo público encontrado',
            }
        )

    # 2) Tentar scraping do perfil público
    logs.append({'fonte': 'Instagram — Perfil', 'status': 'buscando'})
    try:
        url = f'https://www.instagram.com/{username}/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'pt-BR,pt;q=0.9',
        }
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)

        if resp.status_code == 200:
            bio_match = re.search(r'"biography":"(.*?)"', resp.text)
            if bio_match:
                bio = (
                    bio_match.group(1)
                    .encode()
                    .decode('unicode_escape', errors='ignore')
                )
                if len(bio) > 10:
                    posts.append(
                        {
                            'texto': f'Bio Instagram: {bio}',
                            'fonte': 'Instagram — Bio',
                            'url': f'https://instagram.com/{username}',
                        }
                    )
                    fontes['Instagram — Bio'] = 1

            followers = re.search(
                r'"edge_followed_by":\{"count":(\d+)\}', resp.text
            )
            following = re.search(
                r'"edge_follow":\{"count":(\d+)\}', resp.text
            )
            if followers:
                fontes['Instagram — Seguidores'] = int(followers.group(1))
            if following:
                fontes['Instagram — Seguindo'] = int(following.group(1))

            texto_page = re.sub(r'<[^>]+>', ' ', resp.text).lower()
            for fig_user, (fig_nome, fig_score) in FIGURAS_POLITICAS.items():
                if fig_user in texto_page or fig_nome.lower() in texto_page:
                    seguindo_politicos.append(
                        {
                            'username': fig_user,
                            'nome': fig_nome,
                            'score': fig_score,
                            'descricao': '',
                        }
                    )

            logs.append(
                {
                    'fonte': 'Instagram — Perfil',
                    'status': 'ok',
                    'msg': 'Perfil público acessado',
                }
            )
        else:
            logs.append(
                {
                    'fonte': 'Instagram — Perfil',
                    'status': 'aviso',
                    'msg': f'HTTP {resp.status_code} — perfil pode ser privado',
                }
            )
    except Exception as e:
        logs.append(
            {
                'fonte': 'Instagram — Perfil',
                'status': 'aviso',
                'msg': f'Não foi possível acessar o perfil: {str(e)[:60]}',
            }
        )

    if seguindo_politicos:
        fontes['Instagram — Figuras detectadas'] = len(seguindo_politicos)

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    return resultado


def coletar_facebook(username, nome_completo):
    """Coleta dados do Facebook: busca web por perfil, publicações, curtidas."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}

    # 1) Busca web por perfil Facebook
    logs.append({'fonte': 'Facebook — Busca Web', 'status': 'buscando'})
    queries = [
        f'site:facebook.com "{username}" política',
        f'facebook "{nome_completo}" publicações política',
        f'"{nome_completo}" facebook posição opinião política',
    ]
    for q in queries:
        resultados = buscar_web(q, max_results=8)
        for r in resultados:
            r['fonte'] = 'Facebook — Busca Web'
        posts.extend(resultados)

    if posts:
        fontes['Facebook — Busca Web'] = len(posts)
        logs.append(
            {
                'fonte': 'Facebook — Busca Web',
                'status': 'ok',
                'qtd': len(posts),
            }
        )
    else:
        logs.append(
            {
                'fonte': 'Facebook — Busca Web',
                'status': 'aviso',
                'msg': 'Nenhum conteúdo público encontrado',
            }
        )

    # 2) Tentar acessar perfil público
    logs.append({'fonte': 'Facebook — Perfil', 'status': 'buscando'})
    try:
        url = f'https://www.facebook.com/{username}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'pt-BR,pt;q=0.9',
        }
        resp = requests.get(
            url, headers=headers, timeout=TIMEOUT, allow_redirects=True
        )

        if resp.status_code == 200:
            texto_page = re.sub(r'<[^>]+>', ' ', resp.text)

            desc_match = re.search(r'"bio":"(.*?)"', resp.text)
            if desc_match:
                bio = (
                    desc_match.group(1)
                    .encode()
                    .decode('unicode_escape', errors='ignore')
                )
                if len(bio) > 10:
                    posts.append(
                        {
                            'texto': f'Bio Facebook: {bio}',
                            'fonte': 'Facebook — Bio',
                            'url': f'https://facebook.com/{username}',
                        }
                    )
                    fontes['Facebook — Bio'] = 1

            texto_lower = texto_page.lower()
            for fig_user, (fig_nome, fig_score) in FIGURAS_POLITICAS.items():
                if fig_user in texto_lower or fig_nome.lower() in texto_lower:
                    seguindo_politicos.append(
                        {
                            'username': fig_user,
                            'nome': fig_nome,
                            'score': fig_score,
                            'descricao': '',
                        }
                    )

            logs.append(
                {
                    'fonte': 'Facebook — Perfil',
                    'status': 'ok',
                    'msg': 'Página pública acessada',
                }
            )
        else:
            logs.append(
                {
                    'fonte': 'Facebook — Perfil',
                    'status': 'aviso',
                    'msg': f'HTTP {resp.status_code} — perfil pode ser privado',
                }
            )
    except Exception as e:
        logs.append(
            {
                'fonte': 'Facebook — Perfil',
                'status': 'aviso',
                'msg': f'Não foi possível acessar: {str(e)[:60]}',
            }
        )

    if seguindo_politicos:
        fontes['Facebook — Figuras detectadas'] = len(seguindo_politicos)

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    return resultado


def coletar_geral(username, nome_completo):
    """Coleta dados gerais: Google News, Wikipédia, busca web genérica."""
    posts = []
    logs = []
    fontes = {}

    # Busca web genérica
    logs.append({'fonte': 'Busca Web Geral', 'status': 'buscando'})
    queries = [
        f'"{nome_completo}" política posição',
        f'@{username} política opinião',
    ]
    for q in queries:
        posts.extend(buscar_web(q, max_results=10))

    if posts:
        fontes['Busca Web Geral'] = len(posts)
        logs.append(
            {'fonte': 'Busca Web Geral', 'status': 'ok', 'qtd': len(posts)}
        )
    else:
        logs.append(
            {
                'fonte': 'Busca Web Geral',
                'status': 'aviso',
                'msg': 'Nenhum resultado',
            }
        )

    # Google News
    logs.append({'fonte': 'Google News', 'status': 'buscando'})
    posts_news = buscar_noticias(nome_completo)
    if posts_news:
        posts.extend(posts_news)
        fontes['Google News'] = len(posts_news)
        logs.append(
            {'fonte': 'Google News', 'status': 'ok', 'qtd': len(posts_news)}
        )
    else:
        logs.append(
            {
                'fonte': 'Google News',
                'status': 'aviso',
                'msg': 'Nenhuma notícia',
            }
        )

    # Wikipédia
    logs.append({'fonte': 'Wikipédia', 'status': 'buscando'})
    posts_wiki = buscar_wikipedia(nome_completo)
    if posts_wiki:
        posts.extend(posts_wiki)
        fontes['Wikipédia'] = len(posts_wiki)
        logs.append(
            {'fonte': 'Wikipédia', 'status': 'ok', 'qtd': len(posts_wiki)}
        )
    else:
        logs.append(
            {'fonte': 'Wikipédia', 'status': 'aviso', 'msg': 'Nenhum artigo'}
        )

    resultado = montar_resultado_plataforma(posts)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    return resultado


# =====================================================
# FUNÇÃO PRINCIPAL
# =====================================================


def executar_analise(handle, nome_completo=None):
    """
    Executa análise completa com resultados POR PLATAFORMA.
    Retorna resultado geral + resultado individual de cada rede social.
    """
    username = handle.lstrip('@').strip()
    if not username:
        return None, 'Handle vazio'

    if not nome_completo:
        nome_completo = username

    # ===== Coletar por plataforma =====
    plataformas = {}

    plataformas['twitter'] = {
        'nome': 'X / Twitter',
        'icone': '🐦',
        'descricao_coleta': 'Tweets publicados, perfis seguidos, bios',
        **coletar_twitter(username, nome_completo),
    }

    plataformas['instagram'] = {
        'nome': 'Instagram',
        'icone': '📸',
        'descricao_coleta': 'Perfil público, curtidas, seguidos',
        **coletar_instagram(username, nome_completo),
    }

    plataformas['facebook'] = {
        'nome': 'Facebook',
        'icone': '👤',
        'descricao_coleta': 'Publicações, curtidas de páginas',
        **coletar_facebook(username, nome_completo),
    }

    # ===== Dados gerais (News, Wiki, Web) =====
    dados_gerais = coletar_geral(username, nome_completo)
    plataformas['geral'] = {
        'nome': 'Web / Notícias',
        'icone': '🌐',
        'descricao_coleta': 'Google News, Wikipédia, busca web',
        **dados_gerais,
    }

    # ===== Resultado combinado =====
    todos_posts = []
    todos_seguindo = []
    todas_fontes = {}
    todos_logs = []

    for key, plat in plataformas.items():
        todos_posts.extend(plat.get('exemplos', []))
        todos_seguindo.extend(plat.get('seguindo_politicos', []))
        for fonte, qtd in plat.get('fontes', {}).items():
            todas_fontes[fonte] = qtd
        todos_logs.extend(plat.get('logs', []))

    total_esq = sum(p.get('pontos_esq', 0) for p in plataformas.values())
    total_dir = sum(p.get('pontos_dir', 0) for p in plataformas.values())
    total = total_esq + total_dir
    total_posts = sum(p.get('total_posts', 0) for p in plataformas.values())

    # Combinar palavras-chave
    todas_palavras_esq = []
    todas_palavras_dir = []
    for p in plataformas.values():
        for palavra, freq in p.get('top_palavras_esq', []):
            todas_palavras_esq.extend([palavra] * freq)
        for palavra, freq in p.get('top_palavras_dir', []):
            todas_palavras_dir.extend([palavra] * freq)

    # Deduplicar seguindo
    seen = set()
    seguindo_unicos = []
    for fig in todos_seguindo:
        if fig['username'] not in seen:
            seen.add(fig['username'])
            seguindo_unicos.append(fig)

    figuras_esq = list(
        set(f for p in plataformas.values() for f in p.get('figuras_esq', []))
    )[:15]
    figuras_dir = list(
        set(f for p in plataformas.values() for f in p.get('figuras_dir', []))
    )[:15]

    base = {
        'handle': f'@{username}',
        'nome': nome_completo,
        'total_posts': total_posts,
        'fontes': todas_fontes,
        'logs': todos_logs,
        'exemplos': todos_posts[:15],
        'tem_api_twitter': bool(TWITTER_BEARER_TOKEN),
        'seguindo_politicos': seguindo_unicos,
        'figuras_esq': figuras_esq,
        'figuras_dir': figuras_dir,
        'plataformas': plataformas,
    }

    if total == 0:
        base.update(
            {
                'classificacao': 'INCONCLUSIVO',
                'descricao': 'Não foi possível encontrar dados políticos suficientes.',
                'esquerda_pct': 0,
                'direita_pct': 0,
                'confianca': 'NENHUMA',
                'top_palavras_esq': [],
                'top_palavras_dir': [],
                'cor': '#888888',
                'pontos_esq': 0,
                'pontos_dir': 0,
            }
        )
        return base, None

    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    classe, descricao, confianca, cor = classificar(pct_esq, pct_dir, total)

    base.update(
        {
            'classificacao': classe,
            'descricao': descricao,
            'esquerda_pct': round(pct_esq, 1),
            'direita_pct': round(pct_dir, 1),
            'confianca': confianca,
            'top_palavras_esq': Counter(todas_palavras_esq).most_common(10),
            'top_palavras_dir': Counter(todas_palavras_dir).most_common(10),
            'cor': cor,
            'pontos_esq': total_esq,
            'pontos_dir': total_dir,
        }
    )

    return base, None
