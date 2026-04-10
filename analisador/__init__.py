"""
ANÁLISE POLÍTICA — Pacote principal.
Executa a coleta de todas as plataformas SIMULTANEAMENTE via ThreadPoolExecutor,
reduzindo drasticamente o tempo de análise total.
"""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from .analise import classificar
from .dados import TWITTER_BEARER_TOKEN
from .facebook import coletar_facebook
from .geral import coletar_geral
from .instagram import coletar_instagram
from .twitter import coletar_twitter

__all__ = ['executar_analise']

_PLATAFORMA_NAO_PESQUISADA = {
    'total_posts': 0,
    'classificacao': 'NÃO PESQUISADO',
    'descricao': 'Esta rede não foi selecionada para análise',
    'esquerda_pct': 0,
    'direita_pct': 0,
    'confianca': 'NENHUMA',
    'cor': '#888888',
    'pontos_esq': 0,
    'pontos_dir': 0,
    'top_palavras_esq': [],
    'top_palavras_dir': [],
    'seguindo_politicos': [],
    'figuras_esq': [],
    'figuras_dir': [],
    'evidencias': [],
    'exemplos': [],
    'fontes': {},
    'pulado': True,
}


def executar_analise(handle, nome_completo=None, redes_selecionadas=None):
    """
    Executa análise completa com resultados POR PLATAFORMA.
    As plataformas selecionadas são coletadas SIMULTANEAMENTE.
    Retorna resultado geral + resultado individual de cada rede social.

    redes_selecionadas: lista de redes para pesquisar ('twitter', 'instagram', 'facebook')
    """
    username = handle.lstrip('@').strip()
    if not username:
        return None, 'Handle vazio'

    if not nome_completo:
        nome_completo = username

    if redes_selecionadas is None:
        redes_selecionadas = ['twitter', 'instagram', 'facebook']

    # Mapa: chave -> (função de coleta, metadata da plataforma)
    coletores = {
        'twitter': (
            coletar_twitter,
            {'nome': 'X / Twitter', 'icone': '🐦', 'descricao_coleta': 'Tweets publicados, perfis seguidos, bios'},
        ),
        'instagram': (
            coletar_instagram,
            {'nome': 'Instagram', 'icone': '📸', 'descricao_coleta': 'Perfil público, curtidas, seguidos'},
        ),
        'facebook': (
            coletar_facebook,
            {'nome': 'Facebook', 'icone': '👤', 'descricao_coleta': 'Publicações, curtidas de páginas'},
        ),
    }

    plataformas = {}

    # Plataformas não selecionadas recebem resultado vazio imediatamente
    for key, (_, meta) in coletores.items():
        if key not in redes_selecionadas:
            plataformas[key] = {
                **meta,
                **_PLATAFORMA_NAO_PESQUISADA,
                'logs': [{'fonte': meta['nome'], 'status': 'aviso', 'msg': 'Rede não selecionada'}],
            }

    # Plataformas selecionadas rodam em paralelo
    tarefas = {
        key: fn
        for key, (fn, _) in coletores.items()
        if key in redes_selecionadas
    }

    with ThreadPoolExecutor(max_workers=len(tarefas) + 1) as executor:
        # Submete todas as tarefas ao mesmo tempo (incluindo coleta geral)
        futures = {
            executor.submit(fn, username, nome_completo): key
            for key, fn in tarefas.items()
        }
        future_geral = executor.submit(coletar_geral, username, nome_completo)

        # Coleta resultados conforme ficam prontos
        for future in as_completed(futures):
            key = futures[future]
            _, meta = coletores[key]
            try:
                resultado = future.result()
            except Exception as e:
                resultado = {
                    **_PLATAFORMA_NAO_PESQUISADA,
                    'classificacao': 'ERRO',
                    'descricao': f'Falha na coleta: {str(e)[:80]}',
                    'logs': [{'fonte': meta['nome'], 'status': 'erro', 'msg': str(e)[:80]}],
                }
            plataformas[key] = {**meta, **resultado}

        # Resultado da coleta geral
        try:
            dados_gerais = future_geral.result()
        except Exception as e:
            dados_gerais = {
                **_PLATAFORMA_NAO_PESQUISADA,
                'classificacao': 'ERRO',
                'descricao': f'Falha na coleta geral: {str(e)[:80]}',
                'logs': [{'fonte': 'Web / Notícias', 'status': 'erro', 'msg': str(e)[:80]}],
            }

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

    for plat in plataformas.values():
        todos_posts.extend(plat.get('exemplos', []))
        todos_seguindo.extend(plat.get('seguindo_politicos', []))
        for fonte, qtd in plat.get('fontes', {}).items():
            todas_fontes[fonte] = qtd
        todos_logs.extend(plat.get('logs', []))

    total_esq = sum(p.get('pontos_esq', 0) for p in plataformas.values())
    total_dir = sum(p.get('pontos_dir', 0) for p in plataformas.values())
    total = total_esq + total_dir
    total_posts = sum(p.get('total_posts', 0) for p in plataformas.values())

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
        base.update({
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
        })
        return base, None

    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    classe, descricao, confianca, cor = classificar(pct_esq, pct_dir, total)

    base.update({
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
    })

    return base, None
