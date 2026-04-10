"""
Coleta de dados do Instagram: scraping com BeautifulSoup, busca web.
Verifica existência do perfil e extrai bio, hashtags, menções e seguidos.
"""

import json
import re

import requests
from bs4 import BeautifulSoup

from .analise import montar_resultado_plataforma
from .dados import FIGURAS_POLITICAS, TIMEOUT
from .utils import buscar_web, filtrar_resultados_username, verificar_perfil_instagram

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
}


def _extrair_json_instagram(html):
    """Extrai dados JSON embutidos no HTML do Instagram."""
    dados = {}

    # Método 1: window._sharedData (formato antigo, ainda funciona às vezes)
    m = re.search(r'window\._sharedData\s*=\s*({.+?});</script>', html)
    if m:
        try:
            shared = json.loads(m.group(1))
            user = (
                shared.get('entry_data', {})
                .get('ProfilePage', [{}])[0]
                .get('graphql', {})
                .get('user', {})
            )
            if user:
                dados['user'] = user
                return dados
        except (json.JSONDecodeError, IndexError, KeyError):
            pass

    # Método 2: JSON-LD (schema.org) — Instagram embute dados do perfil
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        try:
            ld = json.loads(m.group(1))
            if isinstance(ld, dict) and ld.get('@type') == 'ProfilePage':
                dados['ld'] = ld
        except json.JSONDecodeError:
            pass

    # Método 3: Regex direto nos campos JSON embutidos
    bio = re.search(r'"biography"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
    if bio:
        try:
            dados['bio'] = bio.group(1).encode().decode('unicode_escape', errors='ignore')
        except Exception:
            dados['bio'] = bio.group(1)

    fname = re.search(r'"full_name"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
    if fname:
        dados['full_name'] = fname.group(1)

    is_private = re.search(r'"is_private"\s*:\s*(true|false)', html)
    if is_private:
        dados['is_private'] = is_private.group(1) == 'true'

    followers = re.search(r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)', html)
    if followers:
        dados['followers'] = int(followers.group(1))

    following = re.search(r'"edge_follow"\s*:\s*\{\s*"count"\s*:\s*(\d+)', html)
    if following:
        dados['following'] = int(following.group(1))

    # Método 4: meta tags (fallback sempre disponível)
    soup = BeautifulSoup(html, 'lxml')
    og_desc = soup.find('meta', attrs={'property': 'og:description'})
    if og_desc and og_desc.get('content'):
        dados['og_description'] = og_desc['content']

    og_title = soup.find('meta', attrs={'property': 'og:title'})
    if og_title and og_title.get('content'):
        dados['og_title'] = og_title['content']

    # Extrair todos os links de texto visível (nomes, handles)
    texto_visivel = soup.get_text(separator=' ', strip=True)
    dados['texto_pagina'] = texto_visivel

    return dados


def _extrair_mencoes_e_hashtags(texto):
    """Extrai menções (@user) e hashtags (#tag) de um texto."""
    mencoes = re.findall(r'@([A-Za-z0-9_.]{2,40})', texto)
    hashtags = re.findall(r'#([A-Za-z0-9_\u00C0-\u024F]+)', texto)
    return mencoes, hashtags


def coletar_instagram(username, nome_completo):
    """Coleta dados do Instagram com scraping profundo via BeautifulSoup."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}
    privado = False

    # ═══════════════════════════════════════════════════════════════
    # 1) Verificar existência do perfil + scraping com BS4
    # ═══════════════════════════════════════════════════════════════
    logs.append({'fonte': 'Instagram — Perfil', 'status': 'buscando'})
    perfil_existe, perfil_priv, html_perfil = verificar_perfil_instagram(username)

    if not perfil_existe:
        logs.append({
            'fonte': 'Instagram — Perfil',
            'status': 'aviso',
            'msg': f'Perfil @{username} não encontrado no Instagram',
        })
        # Não retorna NÃO ENCONTRADO aqui — ainda tenta buscas web pelo nome
    else:
        privado = perfil_priv
        if privado:
            logs.append({
                'fonte': 'Instagram — Perfil',
                'status': 'aviso',
                'msg': '🔒 Perfil PRIVADO — dados limitados',
            })

        # Extrair dados do HTML com BS4
        dados = _extrair_json_instagram(html_perfil)

        # Bio
        bio = dados.get('bio', '')
        if not bio:
            # Tentar da meta OG description
            og_desc = dados.get('og_description', '')
            if og_desc and len(og_desc) > 10:
                bio = og_desc
        if bio and len(bio) > 5:
            posts.append({
                'texto': f'Bio Instagram: {bio}',
                'fonte': 'Instagram — Bio',
                'url': f'https://instagram.com/{username}',
            })
            fontes['Instagram — Bio'] = 1
            # Analisar menções e hashtags na bio
            mencoes_bio, hashtags_bio = _extrair_mencoes_e_hashtags(bio)
            for mencao in mencoes_bio:
                mencao_l = mencao.lower()
                if mencao_l in FIGURAS_POLITICAS:
                    fig_nome, fig_score = FIGURAS_POLITICAS[mencao_l]
                    seguindo_politicos.append({
                        'username': mencao_l,
                        'nome': fig_nome,
                        'score': fig_score,
                        'descricao': f'Mencionado na bio do Instagram',
                        'fonte_deteccao': 'Instagram Bio (menção)',
                    })

        # Nome completo do perfil
        full_name = dados.get('full_name', '')
        og_title = dados.get('og_title', '')
        if full_name and len(full_name) > 2:
            posts.append({
                'texto': f'Nome no Instagram: {full_name}',
                'fonte': 'Instagram — Nome',
                'url': f'https://instagram.com/{username}',
            })

        # Seguidores/seguindo
        if dados.get('followers'):
            fontes['Instagram — Seguidores'] = dados['followers']
        if dados.get('following'):
            fontes['Instagram — Seguindo'] = dados['following']

        # Buscar figuras políticas no HTML completo
        texto_pagina = dados.get('texto_pagina', '') or ''
        texto_lower = texto_pagina.lower()

        # Também pegar usernames que aparecem como links no HTML
        soup = BeautifulSoup(html_perfil, 'lxml')
        links = soup.find_all('a', href=True)
        hrefs_texto = ' '.join(a.get('href', '') + ' ' + a.get_text() for a in links).lower()
        texto_busca = texto_lower + ' ' + hrefs_texto

        for fig_user, (fig_nome, fig_score) in FIGURAS_POLITICAS.items():
            encontrado = False
            if len(fig_user) >= 4:
                if fig_user in texto_busca:
                    encontrado = True
            if not encontrado and len(fig_nome) >= 5:
                if fig_nome.lower() in texto_busca:
                    encontrado = True
            if encontrado:
                seguindo_politicos.append({
                    'username': fig_user,
                    'nome': fig_nome,
                    'score': fig_score,
                    'descricao': '',
                    'fonte_deteccao': 'Perfil Instagram (scraping BS4)',
                })

        logs.append({
            'fonte': 'Instagram — Perfil',
            'status': 'ok',
            'msg': f"Bio: {'sim' if bio else 'não'}, Figuras: {len(seguindo_politicos)}",
        })

    # ═══════════════════════════════════════════════════════════════
    # 2) Busca web por USERNAME
    # ═══════════════════════════════════════════════════════════════
    logs.append({'fonte': 'Instagram — Busca Web', 'status': 'buscando'})
    queries_user = [
        f'site:instagram.com/{username}',
        f'"instagram.com/{username}"',
        f'"@{username}" instagram',
    ]
    posts_user = []
    for q in queries_user:
        resultados = buscar_web(q, max_results=8)
        for r in resultados:
            r['fonte'] = 'Instagram — Busca Web'
        posts_user.extend(resultados)
    posts_user = filtrar_resultados_username(posts_user, username)
    posts.extend(posts_user)

    # ═══════════════════════════════════════════════════════════════
    # 3) Busca por NOME COMPLETO + contexto político
    # ═══════════════════════════════════════════════════════════════
    tem_nome = nome_completo and nome_completo.lower() != username.lower()
    posts_nome = []
    if tem_nome:
        queries_nome = [
            f'"{nome_completo}" instagram',
            f'"{nome_completo}" política opinião',
            f'"{nome_completo}" posicionamento declaração',
            f'"{nome_completo}" esquerda OR direita OR governo OR oposição',
            f'"{nome_completo}" entrevista OR polêmica OR comentou',
        ]
        for q in queries_nome:
            resultados = buscar_web(q, max_results=8)
            for r in resultados:
                r['fonte'] = 'Instagram — Reportagens'
            posts_nome.extend(resultados)
        posts.extend(posts_nome)

    qtd_total = len(posts_user) + len(posts_nome)
    if qtd_total > 0:
        fontes['Instagram — Busca Web'] = qtd_total
        logs.append({'fonte': 'Instagram — Busca Web', 'status': 'ok', 'qtd': qtd_total})
    else:
        logs.append({
            'fonte': 'Instagram — Busca Web',
            'status': 'aviso',
            'msg': 'Nenhum conteúdo público encontrado',
        })

    # ═══════════════════════════════════════════════════════════════
    # 4) Busca por interações políticas
    # ═══════════════════════════════════════════════════════════════
    logs.append({'fonte': 'Instagram — Interações', 'status': 'buscando'})
    queries_interacoes = [
        f'"@{username}" instagram curtiu comentou segue',
        f'"@{username}" instagram apoio OR apoia OR compartilhou',
    ]
    if tem_nome:
        queries_interacoes.extend([
            f'"{nome_completo}" instagram compartilhou repostou',
            f'"{nome_completo}" instagram política OR político OR deputado OR senador',
        ])
    posts_interacoes = []
    for q in queries_interacoes:
        resultados = buscar_web(q, max_results=5)
        for r in resultados:
            r['fonte'] = 'Instagram — Interações'
        posts_interacoes.extend(resultados)
    posts_interacoes = filtrar_resultados_username(posts_interacoes, username)

    if posts_interacoes:
        posts.extend(posts_interacoes)
        fontes['Instagram — Interações'] = len(posts_interacoes)
        logs.append({
            'fonte': 'Instagram — Interações',
            'status': 'ok',
            'qtd': len(posts_interacoes),
        })
    else:
        logs.append({
            'fonte': 'Instagram — Interações',
            'status': 'aviso',
            'msg': 'Nenhuma interação encontrada',
        })

    # ═══════════════════════════════════════════════════════════════
    # 5) Tentar buscar posts recentes via páginas alternativas
    # ═══════════════════════════════════════════════════════════════
    if perfil_existe and not privado:
        logs.append({'fonte': 'Instagram — Posts Scraping', 'status': 'buscando'})
        captions_encontradas = 0
        try:
            # Tentar pegar captions de posts via regex no HTML
            captions = re.findall(
                r'"edge_media_to_caption":\{"edges":\[\{"node":\{"text":"((?:[^"\\]|\\.)*)"',
                html_perfil,
            )
            for cap in captions[:20]:
                try:
                    texto = cap.encode().decode('unicode_escape', errors='ignore')
                except Exception:
                    texto = cap
                if len(texto) > 10:
                    posts.append({
                        'texto': texto,
                        'fonte': 'Instagram — Post',
                        'url': f'https://instagram.com/{username}',
                    })
                    captions_encontradas += 1
                    # Analisar menções dentro dos posts
                    mencoes_post, _ = _extrair_mencoes_e_hashtags(texto)
                    for mencao in mencoes_post:
                        mencao_l = mencao.lower()
                        if mencao_l in FIGURAS_POLITICAS:
                            fig_nome, fig_score = FIGURAS_POLITICAS[mencao_l]
                            # Evitar duplicatas
                            if not any(s['username'] == mencao_l for s in seguindo_politicos):
                                seguindo_politicos.append({
                                    'username': mencao_l,
                                    'nome': fig_nome,
                                    'score': fig_score,
                                    'descricao': texto[:80],
                                    'fonte_deteccao': 'Instagram Post (menção)',
                                })
            if captions_encontradas:
                fontes['Instagram — Posts'] = captions_encontradas
                logs.append({
                    'fonte': 'Instagram — Posts Scraping',
                    'status': 'ok',
                    'qtd': captions_encontradas,
                })
            else:
                logs.append({
                    'fonte': 'Instagram — Posts Scraping',
                    'status': 'aviso',
                    'msg': 'Captions não encontradas no HTML (SPA)',
                })
        except Exception as e:
            logs.append({
                'fonte': 'Instagram — Posts Scraping',
                'status': 'aviso',
                'msg': f'Erro ao extrair posts: {str(e)[:60]}',
            })

    if seguindo_politicos:
        fontes['Instagram — Figuras detectadas'] = len(seguindo_politicos)

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    resultado['privado'] = privado
    if privado:
        resultado['aviso_privado'] = (
            '🔒 O perfil do Instagram é PRIVADO. Como não há API pública, '
            'os dados foram coletados via buscas web e podem pertencer a OUTRA PESSOA '
            'com username similar. Os resultados desta rede NÃO são confiáveis — '
            'considere desmarcar o Instagram na pesquisa.'
        )
    return resultado
