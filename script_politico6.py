"""
ANÁLISE POLÍTICA - SOLUÇÃO REALISTA
Versão 6.0 - Com suporte para Twitter API (opcional)
"""

import requests
import re
import json
from datetime import datetime
from collections import Counter
import os

# =========================
# CONFIGURAÇÕES
# =========================

# Chaves de API (configure se tiver)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")  # Cole sua API key aqui

# Palavras-chave
PALAVRAS_ESQUERDA = {
    "democracia", "democratico", "direitos", "humanos", "justica",
    "social", "igualdade", "trabalhador", "sus", "saude", "publica",
    "educacao", "federal", "feminismo", "lgbt", "diversidade",
    "ambiente", "amazonia", "indigena", "pt", "psol", "lula", "dilma"
}

PALAVRAS_DIREITA = {
    "liberdade", "economica", "livre", "mercado", "capitalismo",
    "empreendedor", "privatizacao", "meritocracia", "imposto",
    "familia", "tradicional", "cristaos", "conservador",
    "bolsonaro", "direita", "corrupcao", "petismo"
}

# =========================
# TWITTER API V2 (OFICIAL)
# =========================

def buscar_twitter_api_oficial(username):
    """
    Busca tweets usando a API OFICIAL do Twitter v2
    REQUER: Bearer Token (gratuito para 500k tweets/mês no tier Free)
    """
    print(f"\n🐦 TWITTER (API Oficial v2)")
    
    if not TWITTER_BEARER_TOKEN:
        print("   ⚠️  API Key não configurada")
        print("   ℹ️  Para usar Twitter:")
        print("      1. Acesse: https://developer.twitter.com/")
        print("      2. Crie um projeto (plano Free disponível)")
        print("      3. Copie o Bearer Token")
        print("      4. Configure no script ou variável de ambiente")
        return []
    
    posts = []
    
    try:
        # 1. Buscar ID do usuário
        print(f"   Buscando @{username}...", end=" ", flush=True)
        
        url_user = "https://api.twitter.com/2/users/by/username/" + username
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        
        response = requests.get(url_user, headers=headers, timeout=10)
        
        if response.status_code == 404:
            print("✗ (usuário não encontrado)")
            return []
        
        if response.status_code != 200:
            print(f"✗ (erro {response.status_code})")
            return []
        
        user_data = response.json()
        user_id = user_data["data"]["id"]
        print("✓")
        
        # 2. Buscar tweets
        print(f"   Coletando tweets...", end=" ", flush=True)
        
        url_tweets = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {
            "max_results": 100,  # Free tier: até 100 por request
            "tweet.fields": "created_at,text"
        }
        
        response = requests.get(url_tweets, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            tweets_data = response.json()
            
            for tweet in tweets_data.get("data", []):
                texto = tweet.get("text", "")
                if len(texto) > 20:
                    posts.append({
                        "texto": texto,
                        "fonte": "Twitter",
                        "data": tweet.get("created_at"),
                        "url": f"https://twitter.com/{username}/status/{tweet.get('id')}"
                    })
            
            print(f"✓ {len(posts)} tweets")
        else:
            print(f"✗ (erro {response.status_code})")
    
    except Exception as e:
        print(f"✗ (erro: {str(e)[:40]})")
    
    return posts

# =========================
# MÉTODO ALTERNATIVO - WEB SCRAPING ÉTICO
# =========================

def buscar_twitter_nitter_backup(username):
    """
    Método backup usando Nitter (pode estar instável)
    """
    print(f"\n🐦 TWITTER (método alternativo - Nitter)")
    print(f"   ⚠️  Aviso: Método instável, pode não funcionar")
    
    posts = []
    instancias = [
        "nitter.poast.org",
        "nitter.privacydev.net",
        "nitter.net"
    ]
    
    for instancia in instancias:
        try:
            print(f"   Tentando {instancia}...", end=" ", flush=True)
            url = f"https://{instancia}/{username}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # Extrair tweets
                tweets = re.findall(r'class="tweet-content[^"]*"[^>]*>([^<]+)', html)
                
                for tweet in tweets:
                    texto = re.sub(r'<[^>]+>', '', tweet).strip()
                    if len(texto) > 20:
                        posts.append({
                            "texto": texto,
                            "fonte": "Twitter (Nitter)",
                            "url": f"https://twitter.com/{username}"
                        })
                
                if posts:
                    print(f"✓ {len(posts)} tweets")
                    break
                else:
                    print("✗")
            else:
                print(f"✗")
        except:
            print("✗")
    
    return posts

# =========================
# BUSCA EM NOTÍCIAS
# =========================

def buscar_noticias_sobre_usuario(nome_completo):
    """
    Busca notícias sobre a pessoa usando Google News RSS
    """
    print(f"\n📰 NOTÍCIAS")
    print(f"   Buscando notícias sobre '{nome_completo}'...", end=" ", flush=True)
    
    posts = []
    
    try:
        url = "https://news.google.com/rss/search"
        params = {
            "q": nome_completo,
            "hl": "pt-BR",
            "gl": "BR",
            "ceid": "BR:pt-419"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            # Extrair títulos e descrições
            titulos = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', response.text)
            
            # Pular o primeiro (é o título do feed)
            for titulo in titulos[1:30]:
                if len(titulo) > 20 and nome_completo.lower() in titulo.lower():
                    posts.append({
                        "texto": titulo,
                        "fonte": "Google News",
                        "url": "https://news.google.com/"
                    })
            
            print(f"✓ {len(posts)} notícias")
        else:
            print("✗")
    
    except Exception as e:
        print(f"✗")
    
    return posts

# =========================
# WIKIPÉDIA (PARA FIGURAS PÚBLICAS)
# =========================

def buscar_wikipedia(nome):
    """
    Busca informações na Wikipédia PT
    """
    print(f"\n📖 WIKIPÉDIA")
    print(f"   Buscando '{nome}'...", end=" ", flush=True)
    
    posts = []
    
    try:
        # Buscar página
        url = "https://pt.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": nome,
            "format": "json",
            "utf8": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            resultados = dados.get("query", {}).get("search", [])
            
            if resultados:
                # Pegar o primeiro resultado
                titulo_pagina = resultados[0]["title"]
                
                # Buscar conteúdo
                params_content = {
                    "action": "query",
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "titles": titulo_pagina,
                    "format": "json"
                }
                
                response = requests.get(url, params=params_content, timeout=10)
                
                if response.status_code == 200:
                    dados = response.json()
                    pages = dados.get("query", {}).get("pages", {})
                    
                    for page_id, page_data in pages.items():
                        extract = page_data.get("extract", "")
                        if extract and len(extract) > 100:
                            # Dividir em parágrafos
                            paragrafos = extract.split('\n')
                            for paragrafo in paragrafos[:5]:
                                if len(paragrafo) > 50:
                                    posts.append({
                                        "texto": paragrafo,
                                        "fonte": f"Wikipédia - {titulo_pagina}",
                                        "url": f"https://pt.wikipedia.org/wiki/{titulo_pagina.replace(' ', '_')}"
                                    })
                
                print(f"✓ {len(posts)} parágrafos")
            else:
                print("✗ (não encontrado)")
        else:
            print("✗")
    
    except Exception as e:
        print(f"✗")
    
    return posts

# =========================
# ANÁLISE
# =========================

def normalizar_texto(texto):
    """Remove acentos"""
    texto = texto.lower()
    acentos = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'í': 'i',
        'ó': 'o', 'õ': 'o', 'ô': 'o',
        'ú': 'u', 'ü': 'u', 'ç': 'c'
    }
    for antigo, novo in acentos.items():
        texto = texto.replace(antigo, novo)
    return texto

def analisar_posts(posts):
    """Analisa posts"""
    if not posts:
        return None
    
    total_esq = 0
    total_dir = 0
    palavras_esq = []
    palavras_dir = []
    
    for post in posts:
        texto_norm = normalizar_texto(post.get("texto", ""))
        palavras = re.findall(r'\b\w+\b', texto_norm)
        
        for palavra in palavras:
            if palavra in PALAVRAS_ESQUERDA:
                total_esq += 1
                palavras_esq.append(palavra)
            elif palavra in PALAVRAS_DIREITA:
                total_dir += 1
                palavras_dir.append(palavra)
    
    total = total_esq + total_dir
    
    if total < 3:
        return {
            "classificacao": "SEM CONTEÚDO POLÍTICO DETECTADO",
            "esquerda": 0,
            "direita": 0,
            "confianca": "NENHUMA",
            "total_posts": len(posts)
        }
    
    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    
    diff = abs(pct_esq - pct_dir)
    
    if total < 10:
        confianca = "BAIXA"
    elif total < 25:
        confianca = "MÉDIA"
    else:
        confianca = "ALTA"
    
    if diff < 15:
        classe = "CENTRO"
    elif diff < 35:
        classe = "CENTRO-ESQUERDA" if pct_esq > pct_dir else "CENTRO-DIREITA"
    else:
        classe = "ESQUERDA" if pct_esq > pct_dir else "DIREITA"
    
    return {
        "classificacao": classe,
        "esquerda": round(pct_esq, 1),
        "direita": round(pct_dir, 1),
        "confianca": confianca,
        "total_posts": len(posts),
        "pontos_esq": total_esq,
        "pontos_dir": total_dir,
        "top_palavras_esq": Counter(palavras_esq).most_common(5),
        "top_palavras_dir": Counter(palavras_dir).most_common(5)
    }

# =========================
# BUSCA PRINCIPAL
# =========================

def analisar_figura_publica(nome, username_twitter=None):
    """Analisa uma figura pública"""
    
    print(f"\n{'='*80}")
    print(f"🔍 ANALISANDO: {nome}")
    print(f"{'='*80}")
    
    todos_posts = []
    plataformas = []
    
    # 1. Twitter (se tiver API ou username)
    if username_twitter:
        if TWITTER_BEARER_TOKEN:
            posts_twitter = buscar_twitter_api_oficial(username_twitter)
        else:
            posts_twitter = buscar_twitter_nitter_backup(username_twitter)
        
        if posts_twitter:
            todos_posts.extend(posts_twitter)
            plataformas.append(f"Twitter ({len(posts_twitter)})")
    
    # 2. Notícias
    posts_news = buscar_noticias_sobre_usuario(nome)
    if posts_news:
        todos_posts.extend(posts_news)
        plataformas.append(f"Notícias ({len(posts_news)})")
    
    # 3. Wikipédia
    posts_wiki = buscar_wikipedia(nome)
    if posts_wiki:
        todos_posts.extend(posts_wiki)
        plataformas.append(f"Wikipédia ({len(posts_wiki)})")
    
    # Resultado
    print(f"\n{'='*80}")
    print(f"📊 COLETA FINALIZADA")
    print(f"{'='*80}")
    
    if not todos_posts:
        print("❌ NENHUM DADO ENCONTRADO")
        return None
    
    print(f"✅ Total: {len(todos_posts)} textos coletados")
    print(f"🌐 Fontes: {len(plataformas)}")
    for plat in plataformas:
        print(f"   • {plat}")
    
    # Análise
    print(f"\n📊 Analisando...")
    resultado = analisar_posts(todos_posts)
    
    if resultado:
        resultado["nome"] = nome
        resultado["plataformas"] = plataformas
        exibir_resultado(resultado)
        salvar_resultado(resultado, todos_posts)
    
    return resultado

def exibir_resultado(res):
    """Exibe resultado"""
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO")
    print(f"{'='*80}")
    
    print(f"\n👤 Nome: {res['nome']}")
    print(f"🎯 Classificação: {res['classificacao']}")
    print(f"📈 Confiança: {res['confianca']}")
    
    if res['confianca'] != "NENHUMA":
        print(f"\n📊 DISTRIBUIÇÃO:")
        barra_esq = "█" * int(res['esquerda'] / 2)
        barra_dir = "█" * int(res['direita'] / 2)
        print(f"  🔴 Esquerda: {res['esquerda']:>5.1f}% {barra_esq}")
        print(f"  🔵 Direita:  {res['direita']:>5.1f}% {barra_dir}")
        
        if res.get('top_palavras_esq'):
            print(f"\n🔴 Palavras ESQUERDA:")
            for palavra, freq in res['top_palavras_esq']:
                print(f"     • {palavra}: {freq}x")
        
        if res.get('top_palavras_dir'):
            print(f"\n🔵 Palavras DIREITA:")
            for palavra, freq in res['top_palavras_dir']:
                print(f"     • {palavra}: {freq}x")
    
    print(f"\n📝 Total de textos: {res['total_posts']}")
    print(f"{'='*80}")

def salvar_resultado(resultado, posts):
    """Salva resultado"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_limpo = re.sub(r'[^\w\s-]', '', resultado['nome']).strip().replace(' ', '_')
    filename = f"analise_{nome_limpo}_{timestamp}.json"
    
    dados = {
        **resultado,
        "posts_analisados": posts[:20]  # Salvar apenas os primeiros 20
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Salvo: {filename}")

# =========================
# MENU
# =========================

def menu():
    """Menu principal"""
    global TWITTER_BEARER_TOKEN
    
    # Verificar se tem Twitter API
    tem_twitter_api = bool(TWITTER_BEARER_TOKEN)
    
    while True:
        print(f"\n{'='*80}")
        print("🎯 ANÁLISE POLÍTICA")
        print(f"{'='*80}")
        
        if tem_twitter_api:
            print("✅ Twitter API: CONFIGURADA")
        else:
            print("⚠️  Twitter API: NÃO CONFIGURADA (método backup será usado)")
        
        print("\n1. 🔍 Analisar figura pública")
        print("2. ⚙️  Configurar Twitter API")
        print("3. ℹ️  Informações")
        print("4. 🚪 Sair")
        
        try:
            opcao = input("\nEscolha (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Até logo!")
            break
        
        if opcao == "1":
            print("\n" + "="*80)
            print("📝 DADOS DA PESSOA")
            print("="*80)
            
            try:
                nome = input("Nome completo: ").strip()
                twitter = input("Username no Twitter (ou Enter para pular): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Cancelado")
                continue
            
            if nome:
                analisar_figura_publica(nome, twitter if twitter else None)
            
            input("\nPressione Enter para continuar...")
        
        elif opcao == "2":
            print("\n" + "="*80)
            print("⚙️  CONFIGURAR TWITTER API")
            print("="*80)
            print("\n📋 PASSOS:")
            print("1. Acesse: https://developer.twitter.com/")
            print("2. Crie uma conta de desenvolvedor (FREE)")
            print("3. Crie um App/Project")
            print("4. Copie o Bearer Token")
            print("5. Cole abaixo:\n")
            
            try:
                token = input("Bearer Token: ").strip()
                if token:
                    TWITTER_BEARER_TOKEN = token
                    print("✅ Token configurado!")
                    tem_twitter_api = True
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Cancelado")
            
            input("\nPressione Enter...")
        
        elif opcao == "3":
            print("\n" + "="*80)
            print("ℹ️  INFORMAÇÕES")
            print("="*80)
            print("\n🌐 FONTES DE DADOS:")
            print("   • Twitter - API oficial v2 (requer cadastro FREE)")
            print("   • Google News - RSS público")
            print("   • Wikipédia - API pública")
            print("\n💡 SOBRE TWITTER API:")
            print("   • Plano FREE: 500.000 tweets/mês")
            print("   • Não precisa cartão de crédito")
            print("   • Cadastro em: developer.twitter.com")
            print("\n⚠️  LIMITAÇÕES:")
            print("   • Instagram/Facebook: sem API pública")
            print("   • TikTok: sem API pública")
            print("\n📊 ANÁLISE:")
            print("   • Baseada em palavras-chave políticas")
            print("   • Classifica: Esquerda/Centro/Direita")
            print("="*80)
            input("\nPressione Enter...")
        
        elif opcao == "4":
            print("\n👋 Até logo!")
            break

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print("ANÁLISE POLÍTICA - SOLUÇÃO REALISTA")
    print("Versão 6.0")
    print(f"{'='*80}")
    
    menu()