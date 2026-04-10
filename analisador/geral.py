"""
Coleta geral: Google News, Wikipédia e busca web genérica.
"""

from .analise import montar_resultado_plataforma
from .utils import buscar_noticias, buscar_web, buscar_wikipedia, filtrar_resultados_username


def coletar_geral(username, nome_completo):
    """Coleta dados gerais: Google News, Wikipédia, busca web genérica."""
    posts = []
    logs = []
    fontes = {}

    logs.append({'fonte': 'Busca Web Geral', 'status': 'buscando'})
    tem_nome = nome_completo and nome_completo.lower() != username.lower()

    queries_user = [
        f'"@{username}"',
        f'"{username}" redes sociais',
        f'"{username}" política OR político OR opinião',
    ]
    posts_user = []
    for q in queries_user:
        posts_user.extend(buscar_web(q, max_results=10))
    posts_user = filtrar_resultados_username(posts_user, username)
    posts.extend(posts_user)

    posts_nome = []
    if tem_nome:
        queries_nome = [
            f'"{nome_completo}" política opinião',
            f'"{nome_completo}" esquerda OR direita OR governo OR petista OR bolsonarista',
            f'"{nome_completo}" declaração entrevista posicionamento',
            f'"{nome_completo}" deputado OR senador OR vereador OR prefeito OR governador',
            f'"{nome_completo}" partido OR filiação OR militância OR apoio OR apoiador',
            f'"{nome_completo}" polêmica OR comentou OR criticou OR elogiou',
        ]
        for q in queries_nome:
            posts_nome.extend(buscar_web(q, max_results=10))
        posts.extend(posts_nome)

    qtd_total = len(posts_user) + len(posts_nome)
    if qtd_total > 0:
        fontes['Busca Web Geral'] = qtd_total
        logs.append({'fonte': 'Busca Web Geral', 'status': 'ok', 'qtd': qtd_total})
    else:
        logs.append({'fonte': 'Busca Web Geral', 'status': 'aviso', 'msg': 'Nenhum resultado'})

    # Google News
    logs.append({'fonte': 'Google News', 'status': 'buscando'})
    posts_news = buscar_noticias(nome_completo)
    if posts_news:
        posts.extend(posts_news)
        fontes['Google News'] = len(posts_news)
        logs.append({'fonte': 'Google News', 'status': 'ok', 'qtd': len(posts_news)})
    else:
        logs.append({'fonte': 'Google News', 'status': 'aviso', 'msg': 'Nenhuma notícia'})

    # Wikipédia
    logs.append({'fonte': 'Wikipédia', 'status': 'buscando'})
    posts_wiki = buscar_wikipedia(nome_completo)
    if posts_wiki:
        posts.extend(posts_wiki)
        fontes['Wikipédia'] = len(posts_wiki)
        logs.append({'fonte': 'Wikipédia', 'status': 'ok', 'qtd': len(posts_wiki)})
    else:
        logs.append({'fonte': 'Wikipédia', 'status': 'aviso', 'msg': 'Nenhum artigo'})

    resultado = montar_resultado_plataforma(posts)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    return resultado
