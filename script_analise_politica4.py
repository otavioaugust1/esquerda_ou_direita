"""
ANÁLISE POLÍTICA COM DADOS REAIS DO X/TWITTER
Usa a API pública do Nitter (alternativa aberta ao Twitter)
"""

import requests
import re
import json
import csv
from datetime import datetime
import time
from collections import Counter
import sys

# =========================
# CONFIGURAÇÃO
# =========================
print("=" * 70)
print("ANÁLISE POLÍTICA - DADOS REAIS DO X/TWITTER")
print("=" * 70)
print("Coletando dados públicos via Nitter (alternativa aberta)")
print("=" * 70)

# LISTA DE USUÁRIOS PARA ANÁLISE
USUARIOS_ALVO = [
    "thiago.nigro",      # Vamos testar primeiro
    "LulaOficial",
    "jairbolsonaro",
    "GuilhermeBoulos",
    "CarlaZambelli17",
    "JanonesGov",
    "fiscalizajacurso",
    "alexandre",
    "CamposMello",
    "MajorVitorHugo",
    "0tavioaugust",
    "otavioaugust"

]

# =========================
# DICIONÁRIOS ATUALIZADOS (Baseado em análise real)
# =========================
PALAVRAS_ESQUERDA = {
    # Políticas públicas
    "democracia", "democrático", "direitos", "humanos", "justiça",
    "social", "igualdade", "equidade", "redistribuição", "renda",
    "trabalhador", "trabalhadora", "classe", "trabalhadora",
    
    # Saúde e Educação
    "sus", "saúde", "pública", "universal", "gratuito",
    "educação", "pública", "universidade", "federal",
    
    # Movimentos sociais
    "feminismo", "feminista", "antiracismo", "antiracista",
    "lgbt", "lgbtqia+", "trans", "homofobia", "transfobia",
    "racismo", "machismo", "diversidade", "inclusão",
    
    # Meio Ambiente
    "ambiental", "meio", "ambiente", "sustentável",
    "amazônia", "floresta", "desmatamento", "indígena",
    
    # Críticas
    "fascismo", "fascista", "autoritarismo", "neoliberalismo",
    "privatização", "elite", "burguesia",
    
    # Hashtags
    "#forabolsonaro", "#lula", "#pt", "#elenão", "#mariellepresente",
    "#sus", "#educaçãopública", "#democracia", "#feminismo"
}

PALAVRAS_DIREITA = {
    # Econômicos
    "liberdade", "econômica", "livre", "mercado", "capitalismo",
    "empreendedor", "empreendedorismo", "privatização",
    "estado", "mínimo", "meritocracia", "competitividade",
    
    # Fiscais
    "imposto", "impostos", "tributo", "carga", "tributária",
    "redução", "teto", "gastos", "equilíbrio", "fiscal",
    
    # Valores
    "família", "tradicional", "valores", "cristãos", "cristão",
    "deus", "bíblia", "igreja", "moral", "ética",
    "conservador", "conservadorismo", "patriota", "pátria",
    
    # Segurança
    "segurança", "pública", "lei", "ordem", "autoridade",
    "armamento", "armas", "defesa", "legítima",
    
    # Críticas
    "comunismo", "comunista", "socialismo", "esquerda",
    "esquerdista", "globalismo", "marxismo",
    "populismo", "corrupção", "petismo",
    
    # Hashtags
    "#bolsonaro", "#mito", "#brasilacimadetudo", "#deusacimadetudo",
    "#intervenção", "#escolasempartido", "#foralula",
    "#liberdade", "#livremercado", "#menosimpostos"
}

# =========================
# FUNÇÃO PARA COLETAR TWEETS REAIS
# =========================
def coletar_tweets_reais(usuario, limite=50):
    """
    Coleta tweets REAIS usando Nitter (alternativa aberta ao Twitter)
    """
    tweets = []
    
    # Instâncias do Nitter (escolha uma)
    instancias = [
        "https://nitter.net",          # Principal
        "https://nitter.it",           # Alternativa 1
        "https://nitter.1d4.us",       # Alternativa 2
        "https://nitter.privacydev.net" # Alternativa 3
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for instancia in instancias:
        try:
            print(f"  Tentando coletar de {instancia}/{usuario}...")
            
            # Primeiro, pegar a página do perfil
            url_perfil = f"{instancia}/{usuario}"
            response = requests.get(url_perfil, headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue
            
            # Extrair tweets da página inicial
            html = response.text
            
            # Padrão para encontrar tweets (pode precisar ajuste)
            padroes = [
                r'<div class="tweet-content"[^>]*>([^<]+)</div>',
                r'<div class="tweet-body"[^>]*>.*?<div class="tweet-content"[^>]*>([^<]+)</div>',
                r'class="tweet-content"[^>]*>([^<]+)<',
            ]
            
            for padrao in padroes:
                tweets_encontrados = re.findall(padrao, html, re.DOTALL)
                if tweets_encontrados:
                    for tweet in tweets_encontrados[:limite]:
                        # Limpar HTML e caracteres especiais
                        tweet_limpo = re.sub(r'<[^>]+>', '', tweet)
                        tweet_limpo = re.sub(r'&\w+;', ' ', tweet_limpo)
                        tweet_limpo = tweet_limpo.strip()
                        
                        if tweet_limpo and len(tweet_limpo) > 10:
                            tweets.append(tweet_limpo)
                    
                    if tweets:
                        print(f"  ✓ Coletados {len(tweets)} tweets de @{usuario}")
                        return tweets
            
            # Se não encontrou tweets na página inicial, tentar endpoint de tweets
            try:
                url_tweets = f"{instancia}/{usuario}/rss"
                response_rss = requests.get(url_tweets, headers=headers, timeout=10)
                
                if response_rss.status_code == 200:
                    # Extrair do RSS
                    conteudo_rss = response_rss.text
                    tweets_rss = re.findall(r'<description>[^<]*<!\[CDATA\[(.*?)\]\]></description>', conteudo_rss)
                    
                    for tweet in tweets_rss[:limite]:
                        if tweet and "http" not in tweet and len(tweet) > 20:
                            tweets.append(tweet.strip())
                    
                    if tweets:
                        print(f"  ✓ Coletados {len(tweets)} tweets via RSS de @{usuario}")
                        return tweets
            except:
                pass
                
        except Exception as e:
            print(f"  ✗ Erro com {instancia}: {str(e)[:50]}")
            continue
    
    return tweets

# =========================
# ANÁLISE DE TEXTO
# =========================
def analisar_texto(texto):
    """Analisa um texto e retorna pontuação política"""
    texto = texto.lower()
    
    # Converter texto para análise
    palavras = re.findall(r'\w+', texto)
    hashtags = re.findall(r'#\w+', texto)
    
    # Pontuação
    pontos_esq = 0
    pontos_dir = 0
    
    # Analisar palavras (peso 1)
    for palavra in palavras:
        if palavra in PALAVRAS_ESQUERDA:
            pontos_esq += 1
        elif palavra in PALAVRAS_DIREITA:
            pontos_dir += 1
    
    # Analisar hashtags (peso 2)
    for hashtag in hashtags:
        if hashtag in PALAVRAS_ESQUERDA:
            pontos_esq += 2
        elif hashtag in PALAVRAS_DIREITA:
            pontos_dir += 2
    
    return pontos_esq, pontos_dir

# =========================
# ANÁLISE COMPLETA
# =========================
def analisar_usuario_completo(usuario):
    """Analisa um usuário completo com dados REAIS"""
    print(f"\n🔍 ANALISANDO @{usuario}")
    print("-" * 50)
    
    # Coletar tweets REAIS
    tweets = coletar_tweets_reais(usuario, limite=30)
    
    if not tweets:
        print(f"  ⚠️  Não foi possível coletar tweets para @{usuario}")
        return None
    
    # Analisar cada tweet
    total_esq = 0
    total_dir = 0
    tweets_analisados = 0
    
    for i, tweet in enumerate(tweets[:20], 1):  # Analisar até 20 tweets
        esq, dir = analisar_texto(tweet)
        total_esq += esq
        total_dir += dir
        tweets_analisados += 1
    
    # Calcular resultados
    if tweets_analisados == 0:
        return {
            "usuario": usuario,
            "classificacao": "SEM TWEETS PARA ANÁLISE",
            "esquerda": 0,
            "direita": 0,
            "neutro": 100,
            "tweets_analisados": 0
        }
    
    total_pontos = total_esq + total_dir
    
    if total_pontos == 0:
        return {
            "usuario": usuario,
            "classificacao": "NEUTRO (sem conteúdo político)",
            "esquerda": 0,
            "direita": 0,
            "neutro": 100,
            "tweets_analisados": tweets_analisados
        }
    
    # Calcular porcentagens
    pct_esq = (total_esq / total_pontos) * 100
    pct_dir = (total_dir / total_pontos) * 100
    pct_neutro = max(0, 100 - pct_esq - pct_dir)
    
    # CLASSIFICAÇÃO (regras rigorosas)
    if tweets_analisados < 5:
        classificacao = "POUCOS DADOS (<5 tweets)"
    elif max(pct_esq, pct_dir) < 60:
        if pct_esq > pct_dir:
            classificacao = f"NEUTRO com Inclinação à ESQUERDA ({pct_esq:.1f}%)"
        elif pct_dir > pct_esq:
            classificacao = f"NEUTRO com Inclinação à DIREITA ({pct_dir:.1f}%)"
        else:
            classificacao = "NEUTRO (equilibrado)"
    else:
        if pct_esq > pct_dir:
            classificacao = f"ESQUERDA ({pct_esq:.1f}%)"
        else:
            classificacao = f"DIREITA ({pct_dir:.1f}%)"
    
    # Resultado
    resultado = {
        "usuario": usuario,
        "classificacao": classificacao,
        "esquerda": round(pct_esq, 1),
        "direita": round(pct_dir, 1),
        "neutro": round(pct_neutro, 1),
        "tweets_analisados": tweets_analisados,
        "pontos_esq": total_esq,
        "pontos_dir": total_dir,
        "exemplo_tweet": tweets[0][:100] + "..." if tweets else ""
    }
    
    print(f"  📊 Resultado: {classificacao}")
    print(f"  📈 Esquerda: {pct_esq:.1f}% | Direita: {pct_dir:.1f}% | Neutro: {pct_neutro:.1f}%")
    print(f"  📝 Tweets analisados: {tweets_analisados}")
    
    return resultado

# =========================
# MENU INTERATIVO
# =========================
def menu_principal():
    """Menu principal do sistema"""
    print("\n" + "="*70)
    print("🎯 MENU PRINCIPAL")
    print("="*70)
    print("1. 🔍 Analisar um usuário específico")
    print("2. 📊 Analisar todos os usuários da lista")
    print("3. 🧪 Testar com @thiago.nigro (caso de teste)")
    print("4. 📝 Ver lista de usuários")
    print("5. 🚪 Sair")
    
    try:
        opcao = input("\nEscolha uma opção (1-5): ").strip()
        
        if opcao == "1":
            usuario = input("\nDigite o @ do usuário (sem o @): ").strip()
            if usuario:
                resultado = analisar_usuario_completo(usuario)
                if resultado:
                    exibir_resultado_detalhado(resultado)
        
        elif opcao == "2":
            analisar_lista_completa()
        
        elif opcao == "3":
            print("\n🧪 TESTE ESPECIAL: @thiago.nigro")
            print("(Usuário que declarou ser de direita)")
            resultado = analisar_usuario_completo("thiago.nigro")
            if resultado:
                exibir_resultado_detalhado(resultado)
                print("\n💡 Compare com a declaração pública do usuário!")
        
        elif opcao == "4":
            print("\n📝 LISTA DE USUÁRIOS PARA ANÁLISE:")
            for i, usuario in enumerate(USUARIOS_ALVO, 1):
                print(f"  {i}. @{usuario}")
            print(f"\nTotal: {len(USUARIOS_ALVO)} usuários")
        
        elif opcao == "5":
            print("\n👋 Até logo!")
            return False
        
        else:
            print("Opção inválida!")
        
        return True
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return True

def exibir_resultado_detalhado(resultado):
    """Exibe resultado detalhado"""
    print("\n" + "="*70)
    print("📊 RESULTADO DETALHADO")
    print("="*70)
    print(f"\n👤 Usuário: @{resultado['usuario']}")
    print(f"🏷️  Classificação: {resultado['classificacao']}")
    print(f"\n📈 PORCENTAGENS:")
    print(f"  🔴 Esquerda: {resultado['esquerda']}%")
    print(f"  🔵 Direita:  {resultado['direita']}%")
    print(f"  ⚪ Neutro:   {resultado['neutro']}%")
    print(f"\n📊 DETALHES:")
    print(f"  • Tweets analisados: {resultado['tweets_analisados']}")
    print(f"  • Pontos esquerda: {resultado['pontos_esq']}")
    print(f"  • Pontos direita: {resultado['pontos_dir']}")
    
    if resultado.get('exemplo_tweet'):
        print(f"  • Exemplo de tweet: \"{resultado['exemplo_tweet']}\"")
    
    print("\n" + "="*70)
    print("⚠️  AVISO: Análise baseada em conteúdo público disponível")
    print("="*70)

def analisar_lista_completa():
    """Analisa todos os usuários da lista"""
    print("\n" + "="*70)
    print("📊 ANÁLISE EM LOTE")
    print("="*70)
    
    resultados = []
    
    for i, usuario in enumerate(USUARIOS_ALVO, 1):
        print(f"\n[{i}/{len(USUARIOS_ALVO)}] Processando @{usuario}...")
        
        resultado = analisar_usuario_completo(usuario)
        if resultado:
            resultados.append(resultado)
        
        # Pausa para não sobrecarregar
        time.sleep(2)
    
    # Exibir resumo
    if resultados:
        print("\n" + "="*70)
        print("🎯 RESUMO DA ANÁLISE")
        print("="*70)
        
        print(f"\n{'USUÁRIO':<20} {'ESQUERDA':<10} {'DIREITA':<10} {'CLASSIFICAÇÃO':<30}")
        print("-" * 70)
        
        for res in resultados:
            emoji = "🔴" if "ESQUERDA" in res['classificacao'] else "🔵" if "DIREITA" in res['classificacao'] else "⚪"
            print(f"{emoji} @{res['usuario']:<18} {res['esquerda']:>9.1f}% {res['direita']:>9.1f}% {res['classificacao'][:28]}")
        
        # Salvar resultados
        salvar_resultados(resultados)
        
        # Estatísticas
        esquerda = [r for r in resultados if "ESQUERDA" in r['classificacao']]
        direita = [r for r in resultados if "DIREITA" in r['classificacao']]
        neutros = [r for r in resultados if "NEUTRO" in r['classificacao']]
        
        print(f"\n📈 ESTATÍSTICAS:")
        print(f"  🔴 Esquerda: {len(esquerda)} usuários")
        print(f"  🔵 Direita:  {len(direita)} usuários")
        print(f"  ⚪ Neutros:  {len(neutros)} usuários")

def salvar_resultados(resultados):
    """Salva resultados em arquivo"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV
    with open(f"resultados_reais_{timestamp}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["USUARIO", "CLASSIFICACAO", "ESQUERDA%", "DIREITA%", "NEUTRO%", "TWEETS_ANALISADOS"])
        
        for res in resultados:
            writer.writerow([
                f"@{res['usuario']}",
                res['classificacao'],
                f"{res['esquerda']}%",
                f"{res['direita']}%",
                f"{res['neutro']}%",
                res['tweets_analisados']
            ])
    
    # JSON
    with open(f"detalhes_reais_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Resultados salvos em:")
    print(f"  • resultados_reais_{timestamp}.csv")
    print(f"  • detalhes_reais_{timestamp}.json")

# =========================
# EXECUÇÃO PRINCIPAL
# =========================
def main():
    """Função principal"""
    
    print("\n" + "="*70)
    print("ANÁLISE POLÍTICA COM DADOS REAIS DO X/TWITTER")
    print("="*70)
    print("\nEste script coleta dados PÚBLICOS usando Nitter")
    print("(alternativa de código aberto ao Twitter)")
    print("\n⚠️  AVISOS IMPORTANTES:")
    print("1. Dados são limitados aos tweets públicos visíveis")
    print("2. Alguns perfis podem ter menos tweets disponíveis")
    print("3. A análise é baseada em palavras-chave")
    print("4. Use para fins educacionais/acadêmicos")
    print("="*70)
    
    # Verificar se requests está instalado
    try:
        import requests
    except ImportError:
        print("\n❌ ERRO: A biblioteca 'requests' não está instalada!")
        print("Instale com: pip install requests")
        return
    
    continuar = True
    while continuar:
        continuar = menu_principal()
        
        if continuar:
            input("\nPressione Enter para continuar...")

# =========================
# TESTE RÁPIDO
# =========================
def teste_rapido():
    """Teste rápido com um usuário"""
    print("\n🧪 TESTE RÁPIDO")
    print("-" * 50)
    
    usuario = "thiago.nigro"  # ou outro
    
    print(f"Testando com @{usuario}...")
    resultado = analisar_usuario_completo(usuario)
    
    if resultado:
        print(f"\nResultado: {resultado['classificacao']}")
        print(f"Esquerda: {resultado['esquerda']}%")
        print(f"Direita: {resultado['direita']}%")
        print(f"Baseado em {resultado['tweets_analisados']} tweets")

# =========================
# EXECUTAR
# =========================
if __name__ == "__main__":
    # Para testar rapidamente:
    # teste_rapido()
    
    # Para menu interativo:
    main()