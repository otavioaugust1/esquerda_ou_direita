import json
import logging
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import pandas as pd
import snscrape.modules.instagram as sninstagram
import snscrape.modules.twitter as sntwitter

# =========================
# 0. CONFIGURAÇÃO E LOGGING
# =========================
# LISTA DE USUÁRIOS A ANALISAR (adicione quantos quiser)
USUARIOS_ALVO = [
    'LulaOficial',  # Exemplo esquerda
    'jairbolsonaro',  # Exemplo direita
    'GuilhermeBoulos',  # Exemplo esquerda
    'CarlaZambelli17',  # Exemplo direita
    'JanonesGov',  # Exemplo esquerda
    'fiscalizajacurso',  # Exemplo direita
    'CamposMello',  # Exemplo centro
    'MajorVitorHugo',  # Exemplo direita
    'ErikaHiltonPSOL',  # Exemplo esquerda
    'alexandre',  # Exemplo (ajuste conforme necessidade)
]

LIMITE_POSTS_POR_PLATAFORMA = 200
DIAS_ANALISE = 180  # Analisar últimos 6 meses para mais dados

# Pesos ajustados (repostagens têm peso maior como você pediu)
PESO_POST_AUTORAL = 1.0
PESO_REPOSTAGEM = 2.0  # Aumentado - repostagem é forte sinal de apoio
PESO_HASHTAG = 1.8
PESO_MENCIAO = 1.3
PESO_PERFIL_REFERENCIA = 2.5  # Peso extra para repostar perfis muito marcados

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================
# 1. DICIONÁRIOS SUPER EXPANDIDOS
# =========================
# Dicionários foram significativamente expandidos com base em análises reais
# de discurso político brasileiro nas redes sociais

PALAVRAS_CHAVE_ESQUERDA = {
    # Termos estruturais/programáticos
    'estado',
    'estatal',
    'público',
    'pública',
    'serviço público',
    'serviços públicos',
    'direitos',
    'direito',
    'justiça social',
    'justiça',
    'igualdade',
    'equidade',
    'redistribuição',
    'distribuição de renda',
    'reforma agrária',
    'reforma urbana',
    'democracia',
    'democrático',
    'democrática',
    'participação popular',
    'sus',
    'saúde pública',
    'educação pública',
    'universidade pública',
    'ciência pública',
    'pesquisa pública',
    'cultura pública',
    # Movimentos sociais
    'movimento popular',
    'movimentos populares',
    'movimento social',
    'movimentos sociais',
    'luta',
    'lutas',
    'greve',
    'greves',
    'sindicato',
    'sindicatos',
    'centrais sindicais',
    'mst',
    'mtst',
    'mnlm',
    'movimento negro',
    'movimento feminista',
    'movimento lgbtqia+',
    'feminismo',
    'antirracismo',
    'antiracismo',
    'antifascismo',
    'anti-fascismo',
    # Termos identitários
    'classe trabalhadora',
    'trabalhadores',
    'trabalhadoras',
    'proletariado',
    'oprimidos',
    'oprimidas',
    'minorias',
    'diversidade',
    'inclusão',
    'pluralidade',
    'lgbt',
    'lgbtqia+',
    'lgbtqi+',
    'trans',
    'travesti',
    'homofobia',
    'transfobia',
    'racismo',
    'racista',
    'machismo',
    'machista',
    'patriarcado',
    # Temas ambientais
    'meio ambiente',
    'ambiental',
    'ambientalista',
    'sustentabilidade',
    'amazônia',
    'amazônica',
    'floresta',
    'florestas',
    'desmatamento',
    'indígena',
    'indígenas',
    'quilombola',
    'quilombolas',
    'povos tradicionais',
    # Críticas ao oponente
    'fascismo',
    'fascista',
    'fascistas',
    'autoritarismo',
    'autoritário',
    'neoliberalismo',
    'neoliberal',
    'privatista',
    'privatistas',
    'elite',
    'elites',
    'burguesia',
    'latifundiário',
    'latifundiários',
    # Hashtags ESQUERDA (peso extra)
    '#forabolsonaro',
    '#foragenocida',
    '#bolsonarogenocida',
    '#bolsonaronuncaMais',
    '#lula',
    '#lula2026',
    '#lula13',
    '#pt',
    '#pt13',
    '#ptbrasil',
    '#elenão',
    '#elejamais',
    '#notemernuncamais',
    '#foratemer',
    '#mariellepresente',
    '#mariellevive',
    '#justiçapormarielle',
    '#vaitergolpe',
    '#nãovaitergolpe',
    '#golpenuncaMais',
    '#grevegeral',
    '#brasiliademocratica',
    '#democraciasempre',
    '#sus',
    '#suséumdireito',
    '#defendaosus',
    '#educaçãopública',
    '#educaçãonãoseprivatiza',
    '#foraquiroga',
    '#foraalckmin',
    '#psdbnuncaMais',
    '#antifascismo',
    '#fascismonão',
    '#resistência',
    '#vidasnegrasimportam',
    '#blacklivesmatter',
    '#lutafeminista',
    '#nemumaamenos',
    '#forabolsonaromisógino',
    '#aquecimentoglobal',
    '#mudançasclimáticas',
    '#salveaamazônia',
    '# impeachmentjá',
    '# impeachmentbolsonaro',
}

PALAVRAS_CHAVE_DIREITA = {
    # Termos econômicos/liberais
    'liberdade',
    'liberdades',
    'liberdade econômica',
    'livre mercado',
    'mercado livre',
    'capitalismo',
    'capitalista',
    'empreendedorismo',
    'empreendedor',
    'empreendedora',
    'privatização',
    'privatizações',
    'desestatização',
    'desestatizações',
    'estado mínimo',
    'governo mínimo',
    'meritocracia',
    'meritocrático',
    'meritocrática',
    'competitividade',
    'competitivo',
    'competitiva',
    'produtividade',
    'eficiência',
    # Termos fiscais
    'reforma tributária',
    'imposto',
    'impostos',
    'tributo',
    'tributos',
    'carga tributária',
    'menos impostos',
    'redução de impostos',
    'teto de gastos',
    'controle de gastos',
    'equilíbrio fiscal',
    'responsabilidade fiscal',
    'ajuste fiscal',
    # Termos conservadores/valores
    'família',
    'famílias',
    'tradicional',
    'tradicionais',
    'valores',
    'valores tradicionais',
    'valores cristãos',
    'cristão',
    'cristã',
    'cristãos',
    'deus',
    'bíblia',
    'igreja',
    'religião',
    'moral',
    'moralidade',
    'ética',
    'bons costumes',
    'conservador',
    'conservadora',
    'conservadores',
    'conservadorismo',
    # Segurança/ordem
    'segurança',
    'segurança pública',
    'lei',
    'lei e ordem',
    'ordem',
    'autoridade',
    'disciplina',
    'rigor',
    'punição',
    'pena',
    'penas',
    'armamento',
    'armas',
    'direito de defesa',
    'legítima defesa',
    'combate ao crime',
    'combate à criminalidade',
    # Nacionalismo
    'pátria',
    'patriota',
    'patriótico',
    'patriótica',
    'nacional',
    'nacionalismo',
    'soberania',
    'soberano',
    'soberana',
    'brasil',
    'brasileiro',
    'brasileira',
    'brasileiros',
    'orgulho nacional',
    'amor à pátria',
    # Críticas ao oponente
    'comunismo',
    'comunista',
    'comunistas',
    'socialismo',
    'socialista',
    'esquerda',
    'esquerdista',
    'esquerdistas',
    'esquerdopata',
    'globalismo',
    'globalista',
    'globalistas',
    'marxismo',
    'marxista',
    'cultural',
    'gramscismo',
    'ditadura',
    'ditaduras',
    'populismo',
    'populista',
    'populistas',
    'corrupção',
    'corrupto',
    'corrupta',
    'corruptos',
    'petismo',
    'petista',
    'petistas',
    # Hashtags DIREITA (peso extra)
    '#bolsonaro',
    '#bolsonaro2026',
    '#bolsonaro22',
    '#bolsonaropresidente',
    '#mito',
    '#bolsonaromito',
    '#bolsonaroémito',
    '#brasilacimadetudo',
    '#deusacimadetudo',
    '#deusnocentro',
    '#verdadeeleitoral',
    '#auditoriajá',
    '#fraudeeleitoral',
    '#intervençãomilitar',
    '#intervençãojá',
    '#forçasaramadas',
    '#escolasempartido',
    '#ideologiadegêneronão',
    '#foralula',
    '#lulanuncamais',
    '#ptnuncamais',
    '#petistaladrão',
    '#canetada',
    '#canetadobolsonaro',
    '#liberdade',
    '#livremercado',
    '#menosimpostos',
    '#armamentista',
    '#direitodelegítimadefesa',
    '#conservador',
    '#conservadorismo',
    '#vidasimportam',
    '#alllivesmatter',
    '#foraglobalismo',
    '#nãoaonwo',
    '# impeachmentdolula',
    '#forapt',
    '#volta mito',
    '#mitovoltará',
    '# família',
    '# família tradicional',
}

# PERFIS DE REFERÊNCIA SUPER EXPANDIDOS
PERFIS_REF_ESQUERDA = {
    # Lideranças PT e aliados
    'lulaoficial',
    'gleisi',
    'haddad_fernando',
    'jaqueswagner',
    'ptbrasil',
    'ptnacional',
    'RuiFalcaoPt',
    'ZecaDirceuPT',
    'LindberghFarias',
    'JeanWyllys',
    'ErikaHiltonPSOL',
    # PSOL e partidos de esquerda
    'GuilhermeBoulos',
    'psol50',
    'SampaioMilitante',
    'MarinaHelenaPSOL',
    'TarcisioMota',
    'DavidMirandaRJ',
    'TaliriaPetrone',
    # PCdoB e outros
    'RenatoRabelo',
    'LucianaSantosPCdoB',
    'ManuelaDavila',
    # Governadores e prefeitos
    'FlavioDino',
    'WellingtonDias',
    'RafaelFontana',
    'EduardoPaes',
    'RicardoNunes',
    'BrunoCovas',
    # Movimentos sociais
    'MST_Oficial',
    'MTST_Oficial',
    'RedeSustentabilidade',
    'MarinaSilva',
    'CiroGomes',
    'andreluis',
    # Intelectuais e artistas
    'ConceicaoEvaristo',
    'SueliCarneiro',
    'DjamilaRibeiro',
    'ChicoBuare',
    'CaetanoVeloso',
    'GilbertoGil',
    # Jornalistas/Comunicadores
    'LeonardoSakamoto',
    'JucaKfouri',
    'RenataLoPrete',
    'MiriamLeitao',
    'ReinaldoAzevedoBlog',
}

PERFIS_REF_DIREITA = {
    # Bolsonaro e família
    'jairbolsonaro',
    'FlavioBolsonaro',
    'CarlosBolsonaro',
    'EduardoBolsonaro',
    'MichelBolsonaroRJ',
    # Governo Bolsonaro
    'ernestofarau',
    'SergioMoroOficial',
    'luizhenriquemandetta',
    'TarcisioGF',
    'marcos_pereira',
    'DamaresAlves',
    # Parlamentares direita
    'nikolas_ferreira',
    'CarlaZambelli17',
    'MajorVitorHugo',
    'ChrisTonietto',
    'BiaKicis',
    'CaboDaciolo',
    'FilipeBarros',
    'Jorge_A_C_Gomes',
    'Julio_Cesar_Ribeiro',
    # Partidos de direita
    'pl_22',
    'PLnaCamara',
    'novo',
    'novo30',
    'psl_oficial',
    'democratas',
    'psdb',
    # Movimentos de direita
    'MBLivre',
    'VemPraRua',
    'EndireitaBrasil',
    'BrasilParalelo',
    'TerçaLivree',
    'JovemPanNews',
    # Intelectuais e comentaristas
    'olavo_de_carvalho',
    'Pondé',
    'LuizPhilippeOrleans',
    'LeandroKarnall',
    'ArthurDoVal',
    'NandoMoura',
    'CiroBorges',
    'RodrigoConstantino',
    # Jornalistas/Comunicadores
    'augustusn',
    'CarlaAraujoBlog',
    'BernardoKuster',
    'allanjdosantos',
    'Brasil_247',
    'Metropoles',
}

# =========================
# 2. FUNÇÕES DE ANÁLISE DE TEXTO (OTIMIZADAS)
# =========================
def limpar_e_tokenizar(texto: str) -> List[str]:
    """Limpa o texto e o converte em tokens, mantendo hashtags e menções."""
    if not texto or not isinstance(texto, str):
        return []

    texto = texto.lower()
    texto = re.sub(r'http\S+', '', texto)  # Remove URLs
    texto = re.sub(
        r'pic\.twitter\.com/\S+', '', texto
    )  # Remove links de imagem

    # Mantém hashtags, menções e palavras com acentos
    texto = re.sub(
        r'[^\w\s#@áéíóúãõâêîôûàèìòùçÁÉÍÓÚÃÕÂÊÎÔÛÀÈÌÒÙÇ]', ' ', texto
    )

    # Tokenização mantendo hashtags e @ completos
    tokens = []
    for token in texto.split():
        if token.startswith('#') or token.startswith('@'):
            tokens.append(token)
        else:
            # Remove caracteres especiais remanescentes de palavras comuns
            palavra = re.sub(r'[^\wáéíóúãõâêîôûàèìòùç]', '', token)
            if palavra and len(palavra) > 1:  # Ignora palavras muito curtas
                tokens.append(palavra)

    return tokens


def analisar_tokens(tokens: List[str]) -> Tuple[float, float]:
    """Analisa tokens retornando scores para esquerda e direita."""
    score_esq = 0.0
    score_dir = 0.0

    for token in tokens:
        # Verifica hashtags primeiro (têm peso maior)
        if token.startswith('#'):
            peso = PESO_HASHTAG
            # Remove o # para verificar no dicionário
            token_sem_hash = token[1:].lower()

            if (
                token_sem_hash in PALAVRAS_CHAVE_ESQUERDA
                or token in PALAVRAS_CHAVE_ESQUERDA
            ):
                score_esq += peso
            elif (
                token_sem_hash in PALAVRAS_CHAVE_DIREITA
                or token in PALAVRAS_CHAVE_DIREITA
            ):
                score_dir += peso

        # Verifica menções a perfis de referência
        elif token.startswith('@'):
            perfil = token[1:].lower()
            if perfil in PERFIS_REF_ESQUERDA:
                score_esq += PESO_MENCIAO
            elif perfil in PERFIS_REF_DIREITA:
                score_dir += PESO_MENCIAO

        # Palavras comuns
        else:
            if token in PALAVRAS_CHAVE_ESQUERDA:
                score_esq += 1.0
            elif token in PALAVRAS_CHAVE_DIREITA:
                score_dir += 1.0

    return score_esq, score_dir


# =========================
# 3. FUNÇÕES DE COLETA (COM MELHORIAS)
# =========================
def coletar_posts_twitter(
    usuario: str, limite: int, data_corte: datetime
) -> List[Dict]:
    """Coleta posts do Twitter/X com tratamento de erros aprimorado."""
    posts = []
    data_corte_str = data_corte.strftime('%Y-%m-%d')
    query = f'from:{usuario} since:{data_corte_str}'

    try:
        logger.info(f'Iniciando coleta Twitter para @{usuario}')
        scraper = sntwitter.TwitterSearchScraper(query)

        for i, tweet in enumerate(scraper.get_items()):
            if i >= limite:
                break

            post_info = {
                'plataforma': 'Twitter',
                'data': tweet.date,
                'conteudo': tweet.rawContent
                if hasattr(tweet, 'rawContent')
                else tweet.content,
                'autor_original': usuario,
                'eh_repostagem': tweet.retweetedTweet is not None,
                'autor_repostado': tweet.retweetedTweet.user.username.lower()
                if tweet.retweetedTweet
                else None,
                'hashtags': [f'#{tag}' for tag in tweet.hashtags]
                if tweet.hashtags
                else [],
                'mencoes': [
                    f'@{mention.username}' for mention in tweet.mentionedUsers
                ]
                if tweet.mentionedUsers
                else [],
                'likes': tweet.likeCount if hasattr(tweet, 'likeCount') else 0,
                'reposts': tweet.retweetCount
                if hasattr(tweet, 'retweetCount')
                else 0,
            }
            posts.append(post_info)

            # Pequena pausa para não sobrecarregar
            if i % 50 == 0:
                time.sleep(0.1)

        logger.info(f'Coletados {len(posts)} posts do Twitter para @{usuario}')

    except Exception as e:
        logger.error(
            f'Erro ao coletar do Twitter para @{usuario}: {str(e)[:100]}...'
        )

    return posts


def coletar_posts_instagram(
    usuario: str, limite: int, data_corte: datetime
) -> List[Dict]:
    """Tenta coletar posts do Instagram (suporte limitado)."""
    posts = []

    try:
        logger.info(f'Tentando coleta Instagram para @{usuario}')
        scraper = sninstagram.InstagramUserScraper(usuario)

        for i, post in enumerate(scraper.get_items()):
            if i >= limite:
                break

            if post.date < data_corte:
                continue

            post_info = {
                'plataforma': 'Instagram',
                'data': post.date,
                'conteudo': post.content or '',
                'autor_original': usuario,
                'eh_repostagem': False,  # Instagram não tem repostagem clara via snscrape
                'autor_repostado': None,
                'hashtags': re.findall(r'#(\w+)', post.content)
                if post.content
                else [],
                'mencoes': re.findall(r'@(\w+)', post.content)
                if post.content
                else [],
                'likes': post.likes if hasattr(post, 'likes') else 0,
                'comentarios': post.comments
                if hasattr(post, 'comments')
                else 0,
            }
            posts.append(post_info)

            if i % 20 == 0:
                time.sleep(0.2)

        logger.info(
            f'Coletados {len(posts)} posts do Instagram para @{usuario}'
        )

    except Exception as e:
        logger.warning(
            f'Não foi possível coletar do Instagram para @{usuario}: {str(e)[:100]}...'
        )

    return posts


# =========================
# 4. FUNÇÃO DE ANÁLISE PARA UM USUÁRIO
# =========================
def analisar_usuario(usuario: str) -> Dict:
    """Analisa um único usuário e retorna resultados detalhados."""
    logger.info(f"\n{'='*60}")
    logger.info(f'ANALISANDO USUÁRIO: @{usuario}')
    logger.info(f"{'='*60}")

    data_corte = datetime.now() - timedelta(days=DIAS_ANALISE)

    # Coletar dados de todas as plataformas
    todos_posts = []
    todos_posts.extend(
        coletar_posts_twitter(usuario, LIMITE_POSTS_POR_PLATAFORMA, data_corte)
    )
    todos_posts.extend(
        coletar_posts_instagram(
            usuario, LIMITE_POSTS_POR_PLATAFORMA, data_corte
        )
    )

    if not todos_posts:
        logger.warning(f'Nenhum post coletado para @{usuario}')
        return {
            'usuario': usuario,
            'erro': 'Sem dados públicos disponíveis',
            'classificacao': 'Indeterminado (sem dados)',
            'esquerda': 0,
            'direita': 0,
            'neutro': 100,
            'total_posts': 0,
            'plataformas_analisadas': [],
        }

    # Processar análise
    score_total_esq = 0.0
    score_total_dir = 0.0
    posts_com_conteudo = 0
    posts_repostados = 0
    dados_detalhados = []

    for post in todos_posts:
        peso_post = PESO_POST_AUTORAL
        autor_avaliado = usuario.lower()

        # ANÁLISE DE REPOSTAGENS (peso maior)
        if post['eh_repostagem'] and post['autor_repostado']:
            peso_post = PESO_REPOSTAGEM
            posts_repostados += 1
            autor_repostado = post['autor_repostado'].lower()

            # Se repostar perfil de referência, sinal forte
            if autor_repostado in PERFIS_REF_ESQUERDA:
                score_total_esq += PESO_PERFIL_REFERENCIA * peso_post
                continue
            elif autor_repostado in PERFIS_REF_DIREITA:
                score_total_dir += PESO_PERFIL_REFERENCIA * peso_post
                continue

        # ANÁLISE DE TEXTO
        tokens = limpar_e_tokenizar(post['conteudo'])
        if tokens:  # Só analisa se houver conteúdo
            posts_com_conteudo += 1
            score_esq, score_dir = analisar_tokens(tokens)

            # Adicionar análise de hashtags e menções específicas
            for hashtag in post.get('hashtags', []):
                if hashtag.lower() in PALAVRAS_CHAVE_ESQUERDA:
                    score_esq += PESO_HASHTAG
                elif hashtag.lower() in PALAVRAS_CHAVE_DIREITA:
                    score_dir += PESO_HASHTAG

            for mencao in post.get('mencoes', []):
                mencao_limpa = mencao.replace('@', '').lower()
                if mencao_limpa in PERFIS_REF_ESQUERDA:
                    score_esq += PESO_MENCIAO
                elif mencao_limpa in PERFIS_REF_DIREITA:
                    score_dir += PESO_MENCIAO

            score_total_esq += score_esq * peso_post
            score_total_dir += score_dir * peso_post

        # Guardar detalhes para CSV
        dados_detalhados.append(
            {
                'Usuario': usuario,
                'Plataforma': post['plataforma'],
                'Data': post['data'].strftime('%Y-%m-%d %H:%M')
                if isinstance(post['data'], datetime)
                else post['data'],
                'Conteudo': (post['conteudo'][:150] + '...')
                if len(post['conteudo']) > 150
                else post['conteudo'],
                'Tipo': 'Repost' if post['eh_repostagem'] else 'Post Original',
                'Autor_Repostado': post.get('autor_repostado', ''),
                'Score_Esquerda': score_esq if 'score_esq' in locals() else 0,
                'Score_Direita': score_dir if 'score_dir' in locals() else 0,
                'Likes': post.get('likes', 0),
                'Reposts': post.get('reposts', 0),
            }
        )

    # CALCULAR RESULTADOS
    total_score = score_total_esq + score_total_dir

    if total_score == 0:
        resultado = {
            'usuario': usuario,
            'classificacao': 'Neutro (conteúdo não político)',
            'esquerda': 0,
            'direita': 0,
            'neutro': 100,
            'total_posts': len(todos_posts),
            'posts_analisados': posts_com_conteudo,
            'posts_repostados': posts_repostados,
            'plataformas_analisadas': list(
                set([p['plataforma'] for p in todos_posts])
            ),
        }
    else:
        pct_esq = (score_total_esq / total_score) * 100
        pct_dir = (score_total_dir / total_score) * 100

        # Lógica de classificação refinada
        diferenca = abs(pct_esq - pct_dir)

        if total_score < 5:  # Poucos sinais políticos
            classificacao = 'Neutro (pouca atividade política)'
            pct_neutro = 100 - max(pct_esq, pct_dir)
        elif diferenca < 15:  # Muito equilibrado
            if pct_esq > pct_dir:
                classificacao = f'Centro-Esquerda ({pct_esq:.1f}% esq)'
            else:
                classificacao = f'Centro-Direita ({pct_dir:.1f}% dir)'
            pct_neutro = 100 - pct_esq - pct_dir
        elif max(pct_esq, pct_dir) < 60:
            if pct_esq > pct_dir:
                classificacao = (
                    f'Neutro com Inclinação à Esquerda ({pct_esq:.1f}% esq)'
                )
            else:
                classificacao = (
                    f'Neutro com Inclinação à Direita ({pct_dir:.1f}% dir)'
                )
            pct_neutro = 100 - pct_esq - pct_dir
        else:
            if pct_esq > pct_dir:
                classificacao = f'Esquerda ({pct_esq:.1f}%)'
            else:
                classificacao = f'Direita ({pct_dir:.1f}%)'
            pct_neutro = 0

        resultado = {
            'usuario': usuario,
            'classificacao': classificacao,
            'esquerda': round(pct_esq, 2),
            'direita': round(pct_dir, 2),
            'neutro': round(max(0, pct_neutro), 2),
            'total_posts': len(todos_posts),
            'posts_analisados': posts_com_conteudo,
            'posts_repostados': posts_repostados,
            'score_bruto_esquerda': round(score_total_esq, 2),
            'score_bruto_direita': round(score_total_dir, 2),
            'plataformas_analisadas': list(
                set([p['plataforma'] for p in todos_posts])
            ),
        }

    # SALVAR DETALHES
    if dados_detalhados:
        df_detalhes = pd.DataFrame(dados_detalhados)
        nome_arquivo = (
            f"detalhes_{usuario}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        df_detalhes.to_csv(
            nome_arquivo, index=False, encoding='utf-8-sig', sep=';'
        )
        logger.info(f'Detalhes salvos em: {nome_arquivo}')

    return resultado


# =========================
# 5. ANÁLISE EM LOTE (TODOS OS USUÁRIOS)
# =========================
def analisar_multiplos_usuarios(lista_usuarios: List[str]) -> List[Dict]:
    """Analisa múltiplos usuários e retorna resultados consolidados."""
    resultados = []

    print(f"\n{'='*80}")
    print(f'LABORATÓRIO DE ANÁLISE POLÍTICA - REDES SOCIAIS')
    print(f'Período analisado: Últimos {DIAS_ANALISE} dias')
    print(f'Usuários a analisar: {len(lista_usuarios)}')
    print(f"{'='*80}\n")

    for i, usuario in enumerate(lista_usuarios, 1):
        print(f'[{i}/{len(lista_usuarios)}] Analisando @{usuario}...')

        resultado = analisar_usuario(usuario)
        resultados.append(resultado)

        # Pausa para não sobrecarregar as APIs
        time.sleep(2)

    return resultados


# =========================
# 6. EXECUÇÃO PRINCIPAL
# =========================
if __name__ == '__main__':
    # Analisar todos os usuários
    resultados = analisar_multiplos_usuarios(USUARIOS_ALVO)

    # EXIBIR RESULTADOS
    print(f"\n{'='*80}")
    print('RESULTADOS FINAIS DO LABORATÓRIO')
    print(f"{'='*80}")
    print(
        f"{'USUÁRIO':<25} {'ESQUERDA':<10} {'DIREITA':<10} {'NEUTRO':<10} {'CLASSIFICAÇÃO':<30}"
    )
    print(f"{'-'*80}")

    for res in resultados:
        if 'erro' in res:
            print(
                f"@{res['usuario']:<23} {'N/A':<10} {'N/A':<10} {'N/A':<10} {res['classificacao']}"
            )
        else:
            print(
                f"@{res['usuario']:<23} {res['esquerda']:<9.1f}% {res['direita']:<9.1f}% {res['neutro']:<9.1f}% {res['classificacao']:<30}"
            )

    # Salvar resultados consolidados
    df_resultados = pd.DataFrame(resultados)
    nome_resumo = (
        f"RESUMO_LABORATORIO_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    )
    df_resultados.to_csv(
        nome_resumo, index=False, encoding='utf-8-sig', sep=';'
    )

    # Estatísticas gerais
    print(f"\n{'='*80}")
    print('ESTATÍSTICAS DO LABORATÓRIO')
    print(f"{'='*80}")

    esquerda = [
        r
        for r in resultados
        if 'esquerda' in r
        and r['esquerda'] > r['direita']
        and r['esquerda'] > 50
    ]
    direita = [
        r
        for r in resultados
        if 'direita' in r
        and r['direita'] > r['esquerda']
        and r['direita'] > 50
    ]
    neutros = [
        r
        for r in resultados
        if 'esquerda' in r and max(r['esquerda'], r['direita']) < 60
    ]

    print(f'Total de usuários analisados: {len(resultados)}')
    print(f'Classificados como Esquerda: {len(esquerda)}')
    print(f'Classificados como Direita: {len(direita)}')
    print(f'Classificados como Neutros/Inclinados: {len(neutros)}')
    print(
        f"Indeterminados (sem dados): {len([r for r in resultados if 'erro' in r])}"
    )

    # Salvar estatísticas
    with open(
        f"estatisticas_{datetime.now().strftime('%Y%m%d')}.txt",
        'w',
        encoding='utf-8',
    ) as f:
        f.write(
            f"Laboratório de Análise Política - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        )
        f.write(f'Total de usuários: {len(resultados)}\n')
        f.write(f'Esquerda: {len(esquerda)}\n')
        f.write(f'Direita: {len(direita)}\n')
        f.write(f'Neutros/Inclinados: {len(neutros)}\n')
        f.write('\nDetalhes:\n')
        for res in resultados:
            f.write(f"@{res['usuario']}: {res.get('classificacao', 'N/A')}\n")

    print(f"\n{'='*80}")
    print('ARQUIVOS GERADOS:')
    print(f'  • RESUMO_LABORATORIO_*.csv - Resultados consolidados')
    print(f'  • detalhes_*.csv - Análise detalhada por usuário')
    print(f'  • estatisticas_*.txt - Estatísticas gerais')
    print(f"\n{'='*80}")
    print(
        'AVISO LEGAL: Esta é uma análise automatizada baseada em conteúdo público.'
    )
    print(
        'Os resultados indicam tendências no conteúdo PUBLICADO/AMPLIFICADO,'
    )
    print('não sendo um diagnóstico definitivo das convicções pessoais.')
    print(f"{'='*80}")
