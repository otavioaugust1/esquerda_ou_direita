"""
MÓDULO DE ANÁLISE POLÍTICA
Coleta dados públicos de redes sociais e classifica orientação política.
Estratégia principal: cruzar quem a pessoa SEGUE com um banco de figuras políticas conhecidas.
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
# TWITTER / X - API v2
# =========================


def buscar_twitter_api(username):
    """Busca tweets via API oficial do Twitter v2."""
    if not TWITTER_BEARER_TOKEN:
        return [], 'API Key não configurada'

    posts = []
    headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}

    try:
        url_user = f'https://api.twitter.com/2/users/by/username/{username}'
        resp = requests.get(url_user, headers=headers, timeout=TIMEOUT)

        if resp.status_code != 200:
            return [], f'Erro HTTP {resp.status_code}'

        user_data = resp.json()
        if 'data' not in user_data:
            return [], 'Usuário não encontrado'

        user_id = user_data['data']['id']

        url_tweets = f'https://api.twitter.com/2/users/{user_id}/tweets'
        params = {
            'max_results': 100,
            'tweet.fields': 'created_at,text,public_metrics',
        }
        resp = requests.get(
            url_tweets, headers=headers, params=params, timeout=TIMEOUT
        )

        if resp.status_code == 200:
            for tweet in resp.json().get('data', []):
                texto = tweet.get('text', '')
                if len(texto) > 15:
                    posts.append(
                        {
                            'texto': texto,
                            'fonte': 'Twitter/X',
                            'url': f"https://x.com/{username}/status/{tweet.get('id')}",
                        }
                    )

        return posts, None
    except Exception as e:
        return [], str(e)


def buscar_seguidores_twitter_api(username, max_pages=3):
    """
    Busca quem o usuário SEGUE via API oficial do Twitter.
    Cruza com o banco de figuras políticas conhecidas.
    Retorna: (seguindo_politicos, seguindo_textos, erro)
    """
    if not TWITTER_BEARER_TOKEN:
        return [], [], 'API Key não configurada'

    headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}
    seguindo_politicos = []
    seguindo_textos = []

    try:
        url_user = f'https://api.twitter.com/2/users/by/username/{username}'
        params_user = {'user.fields': 'public_metrics,description'}
        resp = requests.get(
            url_user, headers=headers, params=params_user, timeout=TIMEOUT
        )

        if resp.status_code != 200:
            return [], [], f'Erro HTTP {resp.status_code}'

        user_data = resp.json()
        if 'data' not in user_data:
            return [], [], 'Usuário não encontrado'

        user_id = user_data['data']['id']

        # Buscar quem o usuário segue (paginado)
        url_following = f'https://api.twitter.com/2/users/{user_id}/following'
        all_following = []
        next_token = None

        for _ in range(max_pages):
            params = {
                'max_results': 100,
                'user.fields': 'name,username,description',
            }
            if next_token:
                params['pagination_token'] = next_token

            resp = requests.get(
                url_following, headers=headers, params=params, timeout=TIMEOUT
            )

            if resp.status_code != 200:
                break

            data = resp.json()
            all_following.extend(data.get('data', []))
            next_token = data.get('meta', {}).get('next_token')
            if not next_token:
                break

        # Cruzar com banco de figuras políticas
        for user in all_following:
            uname = user.get('username', '').lower()
            nome = user.get('name', '')
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

            # Bio para análise textual
            if desc and len(desc) > 10:
                seguindo_textos.append(
                    {
                        'texto': f'{nome}: {desc}',
                        'fonte': 'Twitter/X (seguindo)',
                        'url': f'https://x.com/{uname}',
                    }
                )

        return seguindo_politicos, seguindo_textos, None

    except Exception as e:
        return [], [], str(e)


# =========================
# NITTER (BACKUP SEM API)
# =========================


def buscar_twitter_nitter(username):
    """Tenta scraping de tweets via Nitter."""
    posts = []
    instancias = [
        'nitter.poast.org',
        'nitter.privacydev.net',
        'nitter.net',
        'nitter.cz',
    ]

    for instancia in instancias:
        try:
            url = f'https://{instancia}/{username}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=TIMEOUT)

            if response.status_code == 200:
                tweets = re.findall(
                    r'class="tweet-content[^"]*"[^>]*>([^<]+)', response.text
                )
                for tweet in tweets:
                    texto = re.sub(r'<[^>]+>', '', tweet).strip()
                    if len(texto) > 15:
                        posts.append(
                            {
                                'texto': texto,
                                'fonte': 'Twitter/X (Nitter)',
                                'url': f'https://x.com/{username}',
                            }
                        )
                if posts:
                    break
        except Exception:
            continue

    return posts


# =========================
# BUSCA WEB (DDGS + FALLBACK)
# =========================


def buscar_web(query, max_results=15):
    """Busca web usando ddgs (lib) com fallback para scraping manual."""
    posts = []

    # Método 1: Biblioteca DDGS (mais confiável)
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

    # Método 2: Bing scraping (fallback)
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
            # Extrair resultados do Bing
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


# =========================
# GOOGLE NEWS RSS
# =========================


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


# =========================
# WIKIPÉDIA
# =========================


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
# ANÁLISE
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

        # Nomes compostos (peso maior)
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
    """Analisa a lista de figuras políticas seguidas (peso forte)."""
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
    diff = abs(pct_esq - pct_dir)

    if total_pontos < 5:
        confianca = 'MUITO BAIXA'
    elif total_pontos < 15:
        confianca = 'BAIXA'
    elif total_pontos < 30:
        confianca = 'MÉDIA'
    else:
        confianca = 'ALTA'

    if total_pontos < 3:
        return 'INCONCLUSIVO', 'Dados insuficientes', confianca, '#888888'

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


# =========================
# FUNÇÃO PRINCIPAL
# =========================


def executar_analise(handle, nome_completo=None):
    """
    Executa a análise completa.
    - handle: @username
    - nome_completo: nome real para buscar notícias/wiki (opcional)
    """
    username = handle.lstrip('@').strip()
    if not username:
        return None, 'Handle vazio'

    if not nome_completo:
        nome_completo = username

    todos_posts = []
    fontes = {}
    logs = []
    seguindo_politicos = []

    # ===== 1. TWITTER / X =====
    if TWITTER_BEARER_TOKEN:
        # Tweets
        logs.append({'fonte': 'Twitter/X (tweets)', 'status': 'buscando'})
        posts_tw, erro_tw = buscar_twitter_api(username)
        if posts_tw:
            todos_posts.extend(posts_tw)
            fontes['Twitter/X (tweets)'] = len(posts_tw)
            logs.append(
                {
                    'fonte': 'Twitter/X (tweets)',
                    'status': 'ok',
                    'qtd': len(posts_tw),
                }
            )
        else:
            logs.append(
                {
                    'fonte': 'Twitter/X (tweets)',
                    'status': 'aviso',
                    'msg': erro_tw or 'Nenhum tweet encontrado',
                }
            )

        # Quem segue — PRINCIPAL para pessoas comuns
        logs.append({'fonte': 'Twitter/X (seguindo)', 'status': 'buscando'})
        seg_pol, seg_textos, erro_seg = buscar_seguidores_twitter_api(username)
        if seg_pol:
            seguindo_politicos = seg_pol
            fontes['Twitter/X (figuras seguidas)'] = len(seg_pol)
            logs.append(
                {
                    'fonte': 'Twitter/X (seguindo)',
                    'status': 'ok',
                    'qtd': len(seg_pol),
                    'msg': f'{len(seg_pol)} figuras políticas identificadas',
                }
            )
        else:
            logs.append(
                {
                    'fonte': 'Twitter/X (seguindo)',
                    'status': 'aviso',
                    'msg': erro_seg or 'Nenhuma figura política identificada',
                }
            )
        if seg_textos:
            todos_posts.extend(seg_textos)
            fontes['Twitter/X (bios seguidos)'] = len(seg_textos)
    else:
        # Sem API – tentar Nitter
        logs.append({'fonte': 'Twitter/X (Nitter)', 'status': 'buscando'})
        posts_nitter = buscar_twitter_nitter(username)
        if posts_nitter:
            todos_posts.extend(posts_nitter)
            fontes['Twitter/X (Nitter)'] = len(posts_nitter)
            logs.append(
                {
                    'fonte': 'Twitter/X (Nitter)',
                    'status': 'ok',
                    'qtd': len(posts_nitter),
                }
            )
        else:
            logs.append(
                {
                    'fonte': 'Twitter/X',
                    'status': 'aviso',
                    'msg': 'API não configurada e Nitter indisponível. Configure TWITTER_BEARER_TOKEN para melhores resultados.',
                }
            )

    # ===== 2. BUSCA WEB (funciona sem API) =====
    logs.append({'fonte': 'Busca Web', 'status': 'buscando'})
    posts_ddg = []

    # Queries variadas para máxima cobertura
    queries_busca = [
        f'"{nome_completo}" política',
        f'@{username} twitter política',
        f'"{nome_completo}" opinião posição',
    ]
    for q in queries_busca:
        posts_ddg.extend(buscar_web(q, max_results=10))

    if posts_ddg:
        todos_posts.extend(posts_ddg)
        fontes['Busca Web'] = len(posts_ddg)
        logs.append(
            {'fonte': 'Busca Web', 'status': 'ok', 'qtd': len(posts_ddg)}
        )
    else:
        logs.append(
            {
                'fonte': 'Busca Web',
                'status': 'aviso',
                'msg': 'Nenhum resultado',
            }
        )

    # ===== 3. GOOGLE NEWS =====
    logs.append({'fonte': 'Google News', 'status': 'buscando'})
    posts_news = buscar_noticias(nome_completo)
    if posts_news:
        todos_posts.extend(posts_news)
        fontes['Google News'] = len(posts_news)
        logs.append(
            {'fonte': 'Google News', 'status': 'ok', 'qtd': len(posts_news)}
        )
    else:
        logs.append(
            {
                'fonte': 'Google News',
                'status': 'aviso',
                'msg': 'Nenhuma notícia encontrada',
            }
        )

    # ===== 4. WIKIPÉDIA =====
    logs.append({'fonte': 'Wikipédia', 'status': 'buscando'})
    posts_wiki = buscar_wikipedia(nome_completo)
    if posts_wiki:
        todos_posts.extend(posts_wiki)
        fontes['Wikipédia'] = len(posts_wiki)
        logs.append(
            {'fonte': 'Wikipédia', 'status': 'ok', 'qtd': len(posts_wiki)}
        )
    else:
        logs.append(
            {
                'fonte': 'Wikipédia',
                'status': 'aviso',
                'msg': 'Nenhum artigo encontrado',
            }
        )

    # ===== ANÁLISE =====

    # Texto (posts + notícias + bios)
    (
        pts_esq_texto,
        pts_dir_texto,
        palavras_esq,
        palavras_dir,
    ) = analisar_por_palavras(todos_posts)

    # Seguidores (quem a pessoa segue) — peso forte
    pts_esq_seg, pts_dir_seg, figuras_esq, figuras_dir = analisar_seguidores(
        seguindo_politicos
    )

    total_esq = pts_esq_texto + pts_esq_seg
    total_dir = pts_dir_texto + pts_dir_seg
    total = total_esq + total_dir

    exemplos = [
        {'texto': p['texto'][:200], 'fonte': p['fonte']}
        for p in todos_posts[:12]
    ]

    base = {
        'handle': f'@{username}',
        'nome': nome_completo,
        'total_posts': len(todos_posts),
        'fontes': fontes,
        'logs': logs,
        'exemplos': exemplos,
        'tem_api_twitter': bool(TWITTER_BEARER_TOKEN),
        'seguindo_politicos': seguindo_politicos,
        'figuras_esq': list(set(figuras_esq))[:10],
        'figuras_dir': list(set(figuras_dir))[:10],
    }

    if total == 0:
        base.update(
            {
                'classificacao': 'INCONCLUSIVO',
                'descricao': 'Não foi possível encontrar dados políticos suficientes. Configure a API do Twitter para analisar quem você segue.',
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
            'top_palavras_esq': Counter(palavras_esq).most_common(10),
            'top_palavras_dir': Counter(palavras_dir).most_common(10),
            'cor': cor,
            'pontos_esq': total_esq,
            'pontos_dir': total_dir,
        }
    )

    return base, None
