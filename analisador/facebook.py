"""
Coleta de dados do Facebook: scraping com BeautifulSoup, busca web.
Verifica existência do perfil e extrai bio, curtidas e menções políticas.
"""

import json
import re

import requests
from bs4 import BeautifulSoup

from .analise import montar_resultado_plataforma
from .dados import FIGURAS_POLITICAS, TIMEOUT
from .utils import buscar_web, filtrar_resultados_username, verificar_perfil_facebook

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}


def _extrair_dados_facebook(html):
    """Extrai dados estruturados do HTML do Facebook via BS4."""
    dados = {}
    soup = BeautifulSoup(html, 'lxml')

    # Meta tags OG
    og_desc = soup.find('meta', attrs={'property': 'og:description'})
    if og_desc and og_desc.get('content'):
        dados['og_description'] = og_desc['content']

    og_title = soup.find('meta', attrs={'property': 'og:title'})
    if og_title and og_title.get('content'):
        dados['og_title'] = og_title['content']

    # Título da página
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        dados['title'] = title_tag.string.strip()

    # Meta description normal
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        dados['meta_description'] = meta_desc['content']

    # Bio via JSON embutido
    bio = re.search(r'"bio"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
    if bio:
        try:
            dados['bio'] = bio.group(1).encode().decode('unicode_escape', errors='ignore')
        except Exception:
            dados['bio'] = bio.group(1)

    # About / intro
    about = re.search(r'"about"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
    if about:
        try:
            dados['about'] = about.group(1).encode().decode('unicode_escape', errors='ignore')
        except Exception:
            dados['about'] = about.group(1)

    # Texto visível da página
    texto_visivel = soup.get_text(separator=' ', strip=True)
    dados['texto_pagina'] = texto_visivel

    # Links na página
    links = soup.find_all('a', href=True)
    dados['links_texto'] = ' '.join(
        (a.get('href', '') + ' ' + a.get_text()) for a in links
    ).lower()

    return dados


def coletar_facebook(username, nome_completo):
    """Coleta dados do Facebook com scraping profundo via BeautifulSoup."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}
    privado = False

    # ═══════════════════════════════════════════════════════════════
    # 1) Verificar existência do perfil + scraping com BS4
    # ═══════════════════════════════════════════════════════════════
    logs.append({'fonte': 'Facebook — Perfil', 'status': 'buscando'})
    perfil_existe, html_perfil = verificar_perfil_facebook(username)

    if not perfil_existe:
        logs.append({
            'fonte': 'Facebook — Perfil',
            'status': 'aviso',
            'msg': f'Perfil @{username} não encontrado no Facebook',
        })
    else:
        dados = _extrair_dados_facebook(html_perfil)

        # Bio / About
        bio = dados.get('bio', '') or dados.get('about', '')
        if not bio:
            og_desc = dados.get('og_description', '')
            meta_desc = dados.get('meta_description', '')
            bio = og_desc if len(og_desc) > len(meta_desc) else meta_desc
        if bio and len(bio) > 5:
            posts.append({
                'texto': f'Bio Facebook: {bio}',
                'fonte': 'Facebook — Bio',
                'url': f'https://facebook.com/{username}',
            })
            fontes['Facebook — Bio'] = 1

        # Nome/título
        nome_fb = dados.get('og_title', '') or dados.get('title', '')
        if nome_fb and len(nome_fb) > 2:
            posts.append({
                'texto': f'Nome no Facebook: {nome_fb}',
                'fonte': 'Facebook — Nome',
                'url': f'https://facebook.com/{username}',
            })

        # Buscar figuras políticas no conteúdo da página
        texto_busca = (
            dados.get('texto_pagina', '').lower()
            + ' '
            + dados.get('links_texto', '')
        )
        for fig_user, (fig_nome, fig_score) in FIGURAS_POLITICAS.items():
            encontrado = False
            if len(fig_user) >= 4 and fig_user in texto_busca:
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
                    'fonte_deteccao': 'Perfil Facebook (scraping BS4)',
                })

        logs.append({
            'fonte': 'Facebook — Perfil',
            'status': 'ok',
            'msg': f"Bio: {'sim' if bio else 'não'}, Figuras: {len(seguindo_politicos)}",
        })

    # ═══════════════════════════════════════════════════════════════
    # 2) Busca web por USERNAME
    # ═══════════════════════════════════════════════════════════════
    logs.append({'fonte': 'Facebook — Busca Web', 'status': 'buscando'})
    queries_user = [
        f'site:facebook.com/{username}',
        f'"facebook.com/{username}"',
        f'"@{username}" facebook OR fb.com',
    ]
    posts_user = []
    for q in queries_user:
        resultados = buscar_web(q, max_results=8)
        for r in resultados:
            r['fonte'] = 'Facebook — Busca Web'
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
            f'"{nome_completo}" facebook',
            f'"{nome_completo}" política opinião declaração',
            f'"{nome_completo}" esquerda OR direita OR governo OR oposição',
            f'"{nome_completo}" entrevista OR polêmica OR comentou OR apoio',
        ]
        for q in queries_nome:
            resultados = buscar_web(q, max_results=8)
            for r in resultados:
                r['fonte'] = 'Facebook — Reportagens'
            posts_nome.extend(resultados)
        posts.extend(posts_nome)

    qtd_total = len(posts_user) + len(posts_nome)
    if qtd_total > 0:
        fontes['Facebook — Busca Web'] = qtd_total
        logs.append({'fonte': 'Facebook — Busca Web', 'status': 'ok', 'qtd': qtd_total})
    else:
        logs.append({
            'fonte': 'Facebook — Busca Web',
            'status': 'aviso',
            'msg': 'Nenhum conteúdo público encontrado',
        })

    # ═══════════════════════════════════════════════════════════════
    # 4) Busca por interações políticas
    # ═══════════════════════════════════════════════════════════════
    logs.append({'fonte': 'Facebook — Interações', 'status': 'buscando'})
    queries_interacoes = [
        f'"@{username}" facebook curtiu compartilhou',
        f'"@{username}" facebook segue OR apoio OR apoia',
    ]
    if tem_nome:
        queries_interacoes.extend([
            f'"{nome_completo}" facebook reação post político',
            f'"{nome_completo}" facebook política OR deputado OR senador OR vereador',
        ])
    posts_interacoes = []
    for q in queries_interacoes:
        resultados = buscar_web(q, max_results=5)
        for r in resultados:
            r['fonte'] = 'Facebook — Interações'
        posts_interacoes.extend(resultados)
    posts_interacoes = filtrar_resultados_username(posts_interacoes, username)

    if posts_interacoes:
        posts.extend(posts_interacoes)
        fontes['Facebook — Interações'] = len(posts_interacoes)
        logs.append({
            'fonte': 'Facebook — Interações',
            'status': 'ok',
            'qtd': len(posts_interacoes),
        })
    else:
        logs.append({
            'fonte': 'Facebook — Interações',
            'status': 'aviso',
            'msg': 'Nenhuma interação encontrada',
        })

    if seguindo_politicos:
        fontes['Facebook — Figuras detectadas'] = len(seguindo_politicos)

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    resultado['privado'] = privado
    if privado:
        resultado['aviso_privado'] = (
            '🔒 O perfil do Facebook é PRIVADO ou inacessível. Como não há API pública, '
            'os dados foram coletados via buscas web e podem pertencer a OUTRA PESSOA '
            'com username similar. Os resultados desta rede NÃO são confiáveis — '
            'considere desmarcar o Facebook na pesquisa.'
        )
    return resultado
