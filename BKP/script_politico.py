"""
ANÁLISE POLÍTICA COM DADOS PÚBLICOS DE REDES SOCIAIS
Versão melhorada - Usa APIs públicas e legais
"""

import csv
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime

import requests

# =========================
# CONFIGURAÇÃO
# =========================
print('=' * 80)
print('ANÁLISE POLÍTICA - DADOS PÚBLICOS DE REDES SOCIAIS')
print('=' * 80)
print('Coletando dados públicos de forma ética e legal')
print('=' * 80)

# USUÁRIOS PARA ANÁLISE (sem @ no início)
USUARIOS_ALVO = [
    'lulaoficial',
    'jairbolsonaro',
    'guilhermeboulos',
    'carlazambelli38',
    'janonesgov',
    'alexandre',
]

# =========================
# DICIONÁRIOS DE PALAVRAS-CHAVE
# =========================
PALAVRAS_ESQUERDA = {
    # Políticas públicas
    'democracia',
    'democratico',
    'direitos',
    'humanos',
    'justica',
    'social',
    'igualdade',
    'equidade',
    'redistribuicao',
    'renda',
    'trabalhador',
    'trabalhadora',
    'classe',
    # Saúde e Educação
    'sus',
    'saude',
    'publica',
    'universal',
    'gratuito',
    'educacao',
    'universidade',
    'federal',
    # Movimentos sociais
    'feminismo',
    'feminista',
    'antirracismo',
    'antirracista',
    'lgbt',
    'lgbtqia',
    'trans',
    'homofobia',
    'transfobia',
    'racismo',
    'machismo',
    'diversidade',
    'inclusao',
    # Meio Ambiente
    'ambiental',
    'ambiente',
    'sustentavel',
    'amazonia',
    'floresta',
    'desmatamento',
    'indigena',
    # Críticas
    'fascismo',
    'fascista',
    'autoritarismo',
    'neoliberalismo',
    'privatizacao',
    'elite',
    'burguesia',
    # Partidos e movimentos
    'pt',
    'psol',
    'pcb',
    'pcdob',
    'lula',
    'dilma',
    # Hashtags
    'forabolsonaro',
    'elenao',
    'mariellepresente',
    'educacaopublica',
    'lutadeclasses',
}

PALAVRAS_DIREITA = {
    # Econômicos
    'liberdade',
    'economica',
    'livre',
    'mercado',
    'capitalismo',
    'empreendedor',
    'empreendedorismo',
    'privatizacao',
    'estado',
    'minimo',
    'meritocracia',
    'competitividade',
    # Fiscais
    'imposto',
    'impostos',
    'tributo',
    'carga',
    'tributaria',
    'reducao',
    'teto',
    'gastos',
    'equilibrio',
    'fiscal',
    # Valores
    'familia',
    'tradicional',
    'valores',
    'cristaos',
    'cristao',
    'deus',
    'biblia',
    'igreja',
    'moral',
    'etica',
    'conservador',
    'conservadorismo',
    'patriota',
    'patria',
    # Segurança
    'seguranca',
    'lei',
    'ordem',
    'autoridade',
    'armamento',
    'armas',
    'defesa',
    'legitima',
    # Críticas
    'comunismo',
    'comunista',
    'socialismo',
    'esquerda',
    'esquerdista',
    'globalismo',
    'marxismo',
    'populismo',
    'corrupcao',
    'petismo',
    # Partidos e movimentos
    'bolsonaro',
    'pl',
    'republicanos',
    'novo',
    # Hashtags
    'mito',
    'brasilacimаdetudo',
    'deusacimadetudo',
    'intervencao',
    'escolasempartido',
    'foralula',
    'livremercado',
    'menosimpostos',
}

# =========================
# FUNÇÕES DE COLETA DE DADOS
# =========================


def coletar_dados_mastodon(usuario, instancia='mastodon.social', limite=20):
    """
    Coleta posts públicos do Mastodon (rede social aberta)
    API pública e documentada: https://docs.joinmastodon.org/
    """
    posts = []

    try:
        # Buscar ID do usuário
        url_busca = f'https://{instancia}/api/v1/accounts/lookup'
        params = {'acct': usuario}
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(
            url_busca, params=params, headers=headers, timeout=10
        )

        if response.status_code == 200:
            dados_usuario = response.json()
            user_id = dados_usuario['id']

            # Buscar posts públicos
            url_posts = (
                f'https://{instancia}/api/v1/accounts/{user_id}/statuses'
            )
            params_posts = {'limit': limite, 'exclude_replies': True}

            response_posts = requests.get(
                url_posts, params=params_posts, headers=headers, timeout=10
            )

            if response_posts.status_code == 200:
                dados_posts = response_posts.json()

                for post in dados_posts:
                    # Remover HTML
                    texto = re.sub(r'<[^>]+>', '', post.get('content', ''))
                    if texto and len(texto) > 10:
                        posts.append(
                            {
                                'texto': texto,
                                'data': post.get('created_at', ''),
                                'favoritos': post.get('favourites_count', 0),
                            }
                        )

                print(f'  ✓ Coletados {len(posts)} posts do Mastodon')
                return posts

    except Exception as e:
        print(f'  ✗ Erro ao coletar do Mastodon: {str(e)[:50]}')

    return posts


def coletar_dados_reddit(usuario, limite=20):
    """
    Coleta posts públicos do Reddit
    API pública: https://www.reddit.com/dev/api/
    """
    posts = []

    try:
        url = f'https://www.reddit.com/user/{usuario}/submitted.json'
        headers = {'User-Agent': 'Mozilla/5.0 (Educational Research Bot)'}
        params = {'limit': limite}

        response = requests.get(
            url, headers=headers, params=params, timeout=10
        )

        if response.status_code == 200:
            dados = response.json()

            for item in dados.get('data', {}).get('children', []):
                post_data = item.get('data', {})
                titulo = post_data.get('title', '')
                texto = post_data.get('selftext', '')

                conteudo = f'{titulo} {texto}'.strip()

                if conteudo and len(conteudo) > 10:
                    posts.append(
                        {
                            'texto': conteudo,
                            'data': datetime.fromtimestamp(
                                post_data.get('created_utc', 0)
                            ),
                            'upvotes': post_data.get('ups', 0),
                        }
                    )

            print(f'  ✓ Coletados {len(posts)} posts do Reddit')
            return posts

    except Exception as e:
        print(f'  ✗ Erro ao coletar do Reddit: {str(e)[:50]}')

    return posts


def coletar_dados_youtube_comments(canal_id, limite=20):
    """
    Placeholder para coleta do YouTube
    Requer API Key (gratuita mas com registro)
    https://developers.google.com/youtube/v3
    """
    print(f'  ⚠️  YouTube requer API Key (gratuita)')
    print(f'     Registre-se em: https://console.cloud.google.com/')
    return []


def buscar_conteudo_publico(termo_busca, plataforma='reddit'):
    """
    Busca conteúdo público relacionado a um termo
    """
    posts = []

    if plataforma == 'reddit':
        try:
            url = 'https://www.reddit.com/search.json'
            params = {'q': termo_busca, 'limit': 25, 'sort': 'relevance'}
            headers = {'User-Agent': 'Mozilla/5.0'}

            response = requests.get(
                url, params=params, headers=headers, timeout=10
            )

            if response.status_code == 200:
                dados = response.json()

                for item in dados.get('data', {}).get('children', []):
                    post_data = item.get('data', {})
                    titulo = post_data.get('title', '')
                    texto = post_data.get('selftext', '')

                    conteudo = f'{titulo} {texto}'.strip()

                    if conteudo and len(conteudo) > 20:
                        posts.append(
                            {
                                'texto': conteudo,
                                'autor': post_data.get('author', ''),
                                'subreddit': post_data.get('subreddit', ''),
                                'upvotes': post_data.get('ups', 0),
                            }
                        )

                print(
                    f"  ✓ Encontrados {len(posts)} posts sobre '{termo_busca}'"
                )

        except Exception as e:
            print(f'  ✗ Erro na busca: {str(e)[:50]}')

    return posts


# =========================
# ANÁLISE DE TEXTO
# =========================


def normalizar_texto(texto):
    """Remove acentos e normaliza texto"""
    texto = texto.lower()
    # Remover acentos
    substituicoes = {
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
    for antigo, novo in substituicoes.items():
        texto = texto.replace(antigo, novo)

    return texto


def analisar_texto(texto):
    """Analisa texto e retorna pontuação política"""
    texto_norm = normalizar_texto(texto)

    # Extrair palavras e hashtags
    palavras = re.findall(r'\b\w+\b', texto_norm)
    hashtags = re.findall(r'#\w+', texto_norm)

    # Pontuação
    pontos_esq = 0
    pontos_dir = 0
    palavras_encontradas_esq = []
    palavras_encontradas_dir = []

    # Analisar palavras (peso 1)
    for palavra in palavras:
        if palavra in PALAVRAS_ESQUERDA:
            pontos_esq += 1
            palavras_encontradas_esq.append(palavra)
        elif palavra in PALAVRAS_DIREITA:
            pontos_dir += 1
            palavras_encontradas_dir.append(palavra)

    # Analisar hashtags (peso 2 - mais significativas)
    for hashtag in hashtags:
        hashtag_limpo = hashtag.replace('#', '')
        if hashtag_limpo in PALAVRAS_ESQUERDA:
            pontos_esq += 2
            palavras_encontradas_esq.append(hashtag)
        elif hashtag_limpo in PALAVRAS_DIREITA:
            pontos_dir += 2
            palavras_encontradas_dir.append(hashtag)

    return {
        'pontos_esq': pontos_esq,
        'pontos_dir': pontos_dir,
        'palavras_esq': palavras_encontradas_esq,
        'palavras_dir': palavras_encontradas_dir,
    }


def classificar_orientacao(pct_esq, pct_dir, total_pontos):
    """Classifica orientação política com base nas porcentagens"""

    if total_pontos < 5:
        return 'INSUFICIENTE (poucos dados políticos)'

    diferenca = abs(pct_esq - pct_dir)

    # Critérios mais rigorosos
    if diferenca < 20:
        if pct_esq > pct_dir:
            return f'CENTRO-ESQUERDA (leve tendência)'
        elif pct_dir > pct_esq:
            return f'CENTRO-DIREITA (leve tendência)'
        else:
            return 'CENTRO (equilibrado)'
    elif diferenca < 40:
        if pct_esq > pct_dir:
            return 'ESQUERDA (moderada)'
        else:
            return 'DIREITA (moderada)'
    else:
        if pct_esq > pct_dir:
            return 'ESQUERDA (forte)'
        else:
            return 'DIREITA (forte)'


def analisar_conteudo(posts):
    """Analisa conjunto de posts"""
    if not posts:
        return None

    total_esq = 0
    total_dir = 0
    palavras_mais_comuns_esq = []
    palavras_mais_comuns_dir = []
    posts_analisados = 0

    for post in posts:
        texto = post.get('texto', '')
        if len(texto) > 10:
            analise = analisar_texto(texto)
            total_esq += analise['pontos_esq']
            total_dir += analise['pontos_dir']
            palavras_mais_comuns_esq.extend(analise['palavras_esq'])
            palavras_mais_comuns_dir.extend(analise['palavras_dir'])
            posts_analisados += 1

    if posts_analisados == 0:
        return None

    total_pontos = total_esq + total_dir

    if total_pontos == 0:
        return {
            'classificacao': 'NEUTRO (sem conteúdo político detectado)',
            'esquerda': 0,
            'direita': 0,
            'neutro': 100,
            'posts_analisados': posts_analisados,
            'confiabilidade': 'BAIXA',
        }

    # Calcular porcentagens
    pct_esq = (total_esq / total_pontos) * 100
    pct_dir = (total_dir / total_pontos) * 100

    # Classificação
    classificacao = classificar_orientacao(pct_esq, pct_dir, total_pontos)

    # Confiabilidade baseada em quantidade de dados
    if posts_analisados < 5:
        confiabilidade = 'MUITO BAIXA'
    elif posts_analisados < 10:
        confiabilidade = 'BAIXA'
    elif posts_analisados < 20:
        confiabilidade = 'MÉDIA'
    else:
        confiabilidade = 'ALTA'

    # Palavras mais frequentes
    counter_esq = Counter(palavras_mais_comuns_esq)
    counter_dir = Counter(palavras_mais_comuns_dir)

    return {
        'classificacao': classificacao,
        'esquerda': round(pct_esq, 1),
        'direita': round(pct_dir, 1),
        'posts_analisados': posts_analisados,
        'pontos_esq': total_esq,
        'pontos_dir': total_dir,
        'confiabilidade': confiabilidade,
        'palavras_chave_esq': counter_esq.most_common(5),
        'palavras_chave_dir': counter_dir.most_common(5),
    }


# =========================
# MENU E INTERFACE
# =========================


def menu_principal():
    """Menu principal"""
    print('\n' + '=' * 80)
    print('🎯 MENU PRINCIPAL')
    print('=' * 80)
    print('1. 🔍 Buscar posts sobre um tema (Reddit)')
    print('2. 👤 Analisar usuário do Reddit')
    print('3. 🐘 Analisar usuário do Mastodon')
    print('4. 📊 Análise comparativa de temas')
    print('5. ℹ️  Informações sobre o projeto')
    print('6. 🚪 Sair')

    return input('\nEscolha uma opção (1-6): ').strip()


def buscar_e_analisar_tema():
    """Busca e analisa posts sobre um tema"""
    print('\n' + '=' * 80)
    print('🔍 BUSCA POR TEMA')
    print('=' * 80)

    tema = input(
        "\nDigite o tema para buscar (ex: 'bolsa familia', 'economia'): "
    ).strip()

    if not tema:
        print('❌ Tema inválido!')
        return

    print(f"\n📡 Buscando posts sobre '{tema}' no Reddit...")
    posts = buscar_conteudo_publico(tema, plataforma='reddit')

    if not posts:
        print('⚠️  Nenhum post encontrado!')
        return

    print(f'\n📊 Analisando {len(posts)} posts...')
    resultado = analisar_conteudo(posts)

    if resultado:
        exibir_resultado(f'Tema: {tema}', resultado)


def analisar_usuario_reddit():
    """Analisa usuário do Reddit"""
    print('\n' + '=' * 80)
    print('👤 ANÁLISE DE USUÁRIO - REDDIT')
    print('=' * 80)

    usuario = input('\nDigite o username (sem u/): ').strip()

    if not usuario:
        print('❌ Username inválido!')
        return

    print(f'\n📡 Coletando posts de u/{usuario}...')
    posts = coletar_dados_reddit(usuario, limite=30)

    if not posts:
        print('⚠️  Não foi possível coletar posts!')
        return

    print(f'\n📊 Analisando {len(posts)} posts...')
    resultado = analisar_conteudo(posts)

    if resultado:
        exibir_resultado(f'Usuário Reddit: u/{usuario}', resultado)


def analisar_usuario_mastodon():
    """Analisa usuário do Mastodon"""
    print('\n' + '=' * 80)
    print('🐘 ANÁLISE DE USUÁRIO - MASTODON')
    print('=' * 80)

    usuario = input('\nDigite o username: ').strip()
    instancia = (
        input('Digite a instância (padrão: mastodon.social): ').strip()
        or 'mastodon.social'
    )

    if not usuario:
        print('❌ Username inválido!')
        return

    print(f'\n📡 Coletando posts de @{usuario}@{instancia}...')
    posts = coletar_dados_mastodon(usuario, instancia=instancia, limite=30)

    if not posts:
        print('⚠️  Não foi possível coletar posts!')
        return

    print(f'\n📊 Analisando {len(posts)} posts...')
    resultado = analisar_conteudo(posts)

    if resultado:
        exibir_resultado(
            f'Usuário Mastodon: @{usuario}@{instancia}', resultado
        )


def analise_comparativa():
    """Análise comparativa de múltiplos temas"""
    print('\n' + '=' * 80)
    print('📊 ANÁLISE COMPARATIVA')
    print('=' * 80)

    temas = ['bolsonaro', 'lula', 'economia', 'educacao']
    resultados = {}

    for tema in temas:
        print(f'\n🔍 Analisando: {tema}')
        posts = buscar_conteudo_publico(tema, plataforma='reddit')

        if posts:
            resultado = analisar_conteudo(posts)
            if resultado:
                resultados[tema] = resultado

        time.sleep(2)  # Respeitar limites de taxa

    # Exibir comparação
    if resultados:
        print('\n' + '=' * 80)
        print('📊 COMPARAÇÃO DE TEMAS')
        print('=' * 80)
        print(
            f"\n{'TEMA':<20} {'ESQUERDA':<12} {'DIREITA':<12} {'CLASSIFICAÇÃO':<30}"
        )
        print('-' * 80)

        for tema, res in resultados.items():
            print(
                f"{tema:<20} {res['esquerda']:>10.1f}% {res['direita']:>10.1f}% {res['classificacao']:<30}"
            )


def exibir_resultado(titulo, resultado):
    """Exibe resultado detalhado"""
    print('\n' + '=' * 80)
    print('📊 RESULTADO DA ANÁLISE')
    print('=' * 80)
    print(f'\n🎯 {titulo}')
    print(f"🏷️  Classificação: {resultado['classificacao']}")
    print(f"📈 Confiabilidade: {resultado['confiabilidade']}")

    print(f'\n📊 DISTRIBUIÇÃO:')
    print(f"  🔴 Esquerda: {resultado['esquerda']:>6.1f}%")
    print(f"  🔵 Direita:  {resultado['direita']:>6.1f}%")

    print(f'\n📝 DETALHES:')
    print(f"  • Posts analisados: {resultado['posts_analisados']}")
    print(f"  • Pontos esquerda: {resultado['pontos_esq']}")
    print(f"  • Pontos direita: {resultado['pontos_dir']}")

    if resultado.get('palavras_chave_esq'):
        print(f'\n🔴 Palavras-chave ESQUERDA:')
        for palavra, freq in resultado['palavras_chave_esq']:
            print(f'     • {palavra}: {freq}x')

    if resultado.get('palavras_chave_dir'):
        print(f'\n🔵 Palavras-chave DIREITA:')
        for palavra, freq in resultado['palavras_chave_dir']:
            print(f'     • {palavra}: {freq}x')

    print('\n' + '=' * 80)


def exibir_informacoes():
    """Exibe informações sobre o projeto"""
    print('\n' + '=' * 80)
    print('ℹ️  INFORMAÇÕES DO PROJETO')
    print('=' * 80)
    print('\n📋 SOBRE:')
    print('Este projeto analisa conteúdo público de redes sociais para')
    print('identificar tendências políticas usando análise de palavras-chave.')
    print('\n🌐 FONTES DE DADOS:')
    print('  • Reddit - API pública sem autenticação')
    print('  • Mastodon - Rede social federada e aberta')
    print('  • YouTube - Requer API key gratuita')
    print('\n⚖️  ÉTICA E LEGALIDADE:')
    print('  • Apenas dados públicos')
    print('  • Respeita termos de uso das plataformas')
    print('  • Não armazena dados pessoais')
    print('  • Finalidade educacional/pesquisa')
    print('\n⚠️  LIMITAÇÕES:')
    print('  • Análise baseada em palavras-chave (não IA avançada)')
    print('  • Depende da disponibilidade de dados públicos')
    print('  • Resultados são indicativos, não definitivos')
    print('  • Contexto e nuances podem ser perdidos')
    print('\n💡 MELHORIAS FUTURAS:')
    print('  • Análise de sentimento com NLP')
    print('  • Integração com mais plataformas')
    print('  • Machine Learning para classificação')
    print('  • Visualizações gráficas')


def main():
    """Função principal"""
    print('\n' + '=' * 80)
    print('ANÁLISE POLÍTICA DE DADOS PÚBLICOS')
    print('Versão 2.0 - Com dados REAIS')
    print('=' * 80)
    print('\n⚠️  AVISO IMPORTANTE:')
    print(
        'Este programa coleta e analisa apenas dados PÚBLICOS de redes sociais.'
    )
    print(
        'Todas as APIs usadas são públicas e não requerem autenticação especial.'
    )
    print('Use apenas para fins educacionais, acadêmicos ou de pesquisa.')
    print('=' * 80)

    continuar = True

    while continuar:
        opcao = menu_principal()

        try:
            if opcao == '1':
                buscar_e_analisar_tema()
            elif opcao == '2':
                analisar_usuario_reddit()
            elif opcao == '3':
                analisar_usuario_mastodon()
            elif opcao == '4':
                analise_comparativa()
            elif opcao == '5':
                exibir_informacoes()
            elif opcao == '6':
                print('\n👋 Até logo!')
                continuar = False
            else:
                print('\n❌ Opção inválida!')

        except KeyboardInterrupt:
            print('\n\n⚠️  Interrompido pelo usuário')
            continuar = False
        except Exception as e:
            print(f'\n❌ Erro: {e}')

        if continuar:
            input('\nPressione Enter para continuar...')


if __name__ == '__main__':
    main()
