"""
Coleta de dados do Twitter/X: API v2, Nitter e busca web.
Verifica existência do perfil ANTES de atribuir dados.
Otimizado para consumo de memória com limite de posts.
"""

import re

import requests

from .analise import montar_resultado_plataforma
from .dados import FIGURAS_POLITICAS, TIMEOUT, TWITTER_BEARER_TOKEN
from .utils import (
    buscar_web,
    filtrar_por_dominio,
    filtrar_resultados_username,
    verificar_perfil_twitter,
)

# Limite máximo de posts por plataforma (para reduzir uso de memória)
_LIMITE_POSTS_POR_PLATAFORMA = 150

_RESULTADO_NAO_ENCONTRADO = {
    'total_posts': 0,
    'classificacao': 'NÃO ENCONTRADO',
    'descricao': 'Este perfil não foi encontrado no X / Twitter',
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
}


def coletar_twitter(username, nome_completo):
    """Coleta dados do Twitter/X: tweets, seguidores, busca web."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}
    perfil_confirmado = False

    # 1) API oficial
    if TWITTER_BEARER_TOKEN:
        headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}

        logs.append({'fonte': 'X — Tweets (API)', 'status': 'buscando'})
        try:
            url_user = f'https://api.twitter.com/2/users/by/username/{username}'
            resp = requests.get(url_user, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 200 and 'data' in resp.json():
                perfil_confirmado = True
                user_id = resp.json()['data']['id']

                url_tweets = f'https://api.twitter.com/2/users/{user_id}/tweets'
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
                            posts.append({
                                'texto': texto,
                                'fonte': 'X — Tweet',
                                'url': f"https://x.com/{username}/status/{tweet.get('id')}",
                            })
                    fontes['X — Tweets'] = len(posts)
                    logs.append({
                        'fonte': 'X — Tweets (API)',
                        'status': 'ok',
                        'qtd': len(posts),
                    })
                else:
                    logs.append({
                        'fonte': 'X — Tweets (API)',
                        'status': 'aviso',
                        'msg': f'HTTP {resp_tw.status_code}',
                    })

                # Seguindo
                logs.append({'fonte': 'X — Seguindo (API)', 'status': 'buscando'})
                url_following = f'https://api.twitter.com/2/users/{user_id}/following'
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
                        url_following, headers=headers, params=p, timeout=TIMEOUT
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
                        fig_nome, score = FIGURAS_POLITICAS[uname]
                        seguindo_politicos.append({
                            'username': uname,
                            'nome': fig_nome,
                            'score': score,
                            'descricao': desc[:120] if desc else '',
                            'fonte_deteccao': 'API Twitter (lista de seguindo)',
                        })
                    if desc and len(desc) > 10:
                        posts.append({
                            'texto': f"{user.get('name', '')}: {desc}",
                            'fonte': 'X — Bio seguido',
                            'url': f'https://x.com/{uname}',
                        })

                if seguindo_politicos:
                    fontes['X — Figuras seguidas'] = len(seguindo_politicos)
                    logs.append({
                        'fonte': 'X — Seguindo (API)',
                        'status': 'ok',
                        'qtd': len(seguindo_politicos),
                        'msg': f'{len(seguindo_politicos)} figuras políticas',
                    })
                else:
                    logs.append({
                        'fonte': 'X — Seguindo (API)',
                        'status': 'aviso',
                        'msg': 'Nenhuma figura política identificada',
                    })
            else:
                logs.append({
                    'fonte': 'X — Tweets (API)',
                    'status': 'aviso',
                    'msg': 'Usuário não encontrado na API',
                })

        except Exception as e:
            logs.append({'fonte': 'X — Tweets (API)', 'status': 'erro', 'msg': str(e)[:80]})

    else:
        # Sem API — VERIFICAR SE O PERFIL EXISTE ANTES de qualquer busca
        logs.append({'fonte': 'X — Verificação', 'status': 'buscando'})
        perfil_confirmado = verificar_perfil_twitter(username)

        if not perfil_confirmado:
            logs.append({
                'fonte': 'X — Verificação',
                'status': 'aviso',
                'msg': f'Perfil @{username} NÃO encontrado no X/Twitter',
            })
            resultado = dict(_RESULTADO_NAO_ENCONTRADO)
            resultado['fontes'] = fontes
            resultado['logs'] = logs
            return resultado

        logs.append({
            'fonte': 'X — Verificação',
            'status': 'ok',
            'msg': f'Perfil @{username} confirmado no X/Twitter',
        })
        perfil_confirmado = True

        # Nitter scraping
        logs.append({'fonte': 'X — Nitter', 'status': 'buscando'})
        instancias = [
            'xcancel.com',
            'nitter.poast.org',
            'nitter.privacydev.net',
            'nitter.net',
            'nitter.cz',
            'nitter.woodland.cafe',
            'nitter.1d4.us',
            'nitter.kavin.rocks',
        ]
        nitter_ok = None
        h = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html',
        }
        for instancia in instancias:
            try:
                url = f'https://{instancia}/{username}'
                response = requests.get(url, headers=h, timeout=TIMEOUT)
                if response.status_code == 200 and 'user not found' not in response.text.lower():
                    tweets = re.findall(
                        r'class="tweet-content[^"]*"[^>]*>([^<]+)',
                        response.text,
                    )
                    for tweet in tweets:
                        texto = re.sub(r'<[^>]+>', '', tweet).strip()
                        if len(texto) > 15:
                            posts.append({
                                'texto': texto,
                                'fonte': 'X — Nitter',
                                'url': f'https://x.com/{username}',
                            })
                    if posts:
                        fontes['X — Nitter'] = len(posts)
                        logs.append({'fonte': 'X — Nitter', 'status': 'ok', 'qtd': len(posts)})
                        nitter_ok = instancia
                        break
            except Exception:
                continue
        if not posts:
            logs.append({'fonte': 'X — Nitter', 'status': 'aviso', 'msg': 'Nitter indisponível'})

        # Nitter — tentar buscar lista de seguindo
        if nitter_ok:
            logs.append({'fonte': 'X — Seguindo (Nitter)', 'status': 'buscando'})
            try:
                url_f = f'https://{nitter_ok}/{username}/following'
                resp_f = requests.get(url_f, headers=h, timeout=TIMEOUT)
                if resp_f.status_code == 200:
                    candidatos = re.findall(
                        r'href="/([a-zA-Z0-9_]{2,15})"', resp_f.text
                    )
                    ignorar = {
                        username.lower(), 'about', 'login', 'search',
                        'settings', 'rss', 'media', 'with_replies',
                    }
                    vistos_nitter = set()
                    for uname in candidatos:
                        uname_l = uname.lower()
                        if uname_l in ignorar or uname_l in vistos_nitter:
                            continue
                        vistos_nitter.add(uname_l)
                        if uname_l in FIGURAS_POLITICAS:
                            fig_nome, fig_score = FIGURAS_POLITICAS[uname_l]
                            seguindo_politicos.append({
                                'username': uname_l,
                                'nome': fig_nome,
                                'score': fig_score,
                                'descricao': '',
                                'fonte_deteccao': 'Nitter (lista de seguindo)',
                            })
                    if seguindo_politicos:
                        fontes['X — Seguindo (Nitter)'] = len(seguindo_politicos)
                        logs.append({
                            'fonte': 'X — Seguindo (Nitter)',
                            'status': 'ok',
                            'qtd': len(seguindo_politicos),
                            'msg': f'{len(seguindo_politicos)} figuras políticas detectadas',
                        })
                    else:
                        logs.append({
                            'fonte': 'X — Seguindo (Nitter)',
                            'status': 'aviso',
                            'msg': 'Nenhuma figura política na lista de seguindo',
                        })
            except Exception as e:
                logs.append({
                    'fonte': 'X — Seguindo (Nitter)',
                    'status': 'aviso',
                    'msg': f'Não foi possível buscar seguindo: {str(e)[:60]}',
                })

    # ═══════════════════════════════════════════════════════════════
    # Busca web ESTRITA (somente domínios x.com / twitter.com)
    # Só roda se o perfil foi confirmado
    # ═══════════════════════════════════════════════════════════════
    if perfil_confirmado:
        logs.append({'fonte': 'X — Busca Web', 'status': 'buscando'})
        queries = [
            f'site:x.com/{username} OR site:twitter.com/{username}',
            f'(site:x.com OR site:twitter.com) "@{username}"',
            f'"x.com/{username}" OR "twitter.com/{username}"',
        ]
        posts_web = []
        for q in queries:
            posts_web.extend(buscar_web(q, max_results=8))

        # FILTRO ESTRITO: apenas URLs de x.com ou twitter.com
        posts_web = filtrar_por_dominio(posts_web, ['x.com', 'twitter.com', 'nitter.'])
        posts_web = filtrar_resultados_username(posts_web, username)

        for p in posts_web:
            p['fonte'] = 'X — Busca Web'
        posts.extend(posts_web)
        if posts_web:
            fontes['X — Busca Web'] = len(posts_web)
            logs.append({'fonte': 'X — Busca Web', 'status': 'ok', 'qtd': len(posts_web)})
        else:
            logs.append({'fonte': 'X — Busca Web', 'status': 'aviso', 'msg': 'Nenhum resultado'})

        # Contexto político (apenas se tem nome completo diferente do handle)
        tem_nome = nome_completo and nome_completo.lower() != username.lower()
        if tem_nome:
            logs.append({'fonte': 'X — Contexto Político', 'status': 'buscando'})
            queries_pol = [
                f'"@{username}" twitter política OR opinião OR posicionamento',
                f'"@{username}" twitter esquerda OR direita OR governo OR oposição',
            ]
            posts_pol = []
            for q in queries_pol:
                posts_pol.extend(buscar_web(q, max_results=6))
            # Filtrar: exigir que o resultado mencione o username
            posts_pol = filtrar_resultados_username(posts_pol, username)
            for p in posts_pol:
                p['fonte'] = 'X — Contexto Político'
            posts.extend(posts_pol)
            if posts_pol:
                fontes['X — Contexto Político'] = len(posts_pol)
                logs.append({'fonte': 'X — Contexto Político', 'status': 'ok', 'qtd': len(posts_pol)})
            else:
                logs.append({'fonte': 'X — Contexto Político', 'status': 'aviso', 'msg': 'Nenhum resultado'})

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    return resultado
