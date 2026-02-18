"""
ANÁLISE POLÍTICA PROFUNDA - BUSCA INTENSIVA EM MÚLTIPLAS REDES
Versão 4.0 - Coleta Profunda e Robusta
"""

import requests
import re
import json
from datetime import datetime
from collections import Counter
import time

# =========================
# PALAVRAS-CHAVE EXPANDIDAS
# =========================
PALAVRAS_ESQUERDA = {
    # Políticas e ideologia
    "democracia", "democratico", "democratica", "direitos", "humanos", 
    "justica", "social", "igualdade", "equidade", "trabalhador", "trabalhadora",
    "trabalhadores", "proletariado", "classe", "operaria",
    
    # Saúde e educação
    "sus", "saude", "publica", "universal", "gratuito", "gratuita",
    "educacao", "universidade", "federal", "publicas",
    
    # Movimentos
    "feminismo", "feminista", "lgbt", "lgbtqia", "diversidade",
    "inclusao", "antirracismo", "antifascismo",
    
    # Economia
    "redistribuicao", "renda", "desigualdade", "pobreza",
    
    # Meio ambiente
    "ambiente", "sustentavel", "amazonia", "floresta", "indigena",
    "climatica", "aquecimento",
    
    # Partidos e líderes
    "pt", "psol", "pcdob", "lula", "dilma", "haddad", "boulos",
    "marielle", "ciro", "gomes",
    
    # Termos críticos
    "fascismo", "fascista", "neoliberalismo", "golpe", "impeachment",
    "privatizacao", "desmonte"
}

PALAVRAS_DIREITA = {
    # Economia
    "liberdade", "economica", "livre", "mercado", "capitalismo",
    "empreendedor", "empreendedorismo", "privatizacao", "privatizar",
    "meritocracia", "competitividade", "iniciativa", "privada",
    
    # Fiscal
    "imposto", "impostos", "tributo", "tributaria", "reducao",
    "teto", "gastos", "responsabilidade", "fiscal",
    
    # Valores
    "familia", "tradicional", "valores", "cristaos", "cristao",
    "deus", "biblia", "igreja", "conservador", "conservadorismo",
    "patriota", "patria", "nacionalismo",
    
    # Segurança
    "seguranca", "publica", "lei", "ordem", "policia",
    "armamento", "armas", "defesa", "legitima",
    
    # Partidos e líderes
    "bolsonaro", "jair", "pl", "republicanos", "novo", "mbl",
    "guedes", "moro", "sergio", "damares",
    
    # Termos críticos
    "comunismo", "comunista", "socialismo", "esquerdista",
    "marxismo", "corrupcao", "petismo", "lulopetismo"
}

# =========================
# FUNÇÕES DE BUSCA APRIMORADAS
# =========================

def buscar_twitter_multiplas_fontes(username):
    """Busca no Twitter/X usando múltiplas estratégias"""
    posts = []
    
    # Remover @ se houver
    username = username.replace('@', '').strip()
    
    print(f"\n   🔄 Tentando múltiplas instâncias Nitter...")
    
    # Lista expandida de instâncias Nitter
    instancias = [
        "nitter.poast.org",
        "nitter.privacydev.net",
        "nitter.net",
        "nitter.it",
        "nitter.unixfox.eu",
        "nitter.1d4.us",
        "nitter.kavin.rocks",
        "nitter.fdn.fr",
        "nitter.namazso.eu"
    ]
    
    for i, instancia in enumerate(instancias, 1):
        try:
            url = f"https://{instancia}/{username}"
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            }
            
            print(f"      [{i}/{len(instancias)}] {instancia}...", end=" ", flush=True)
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                html = response.text
                
                # Múltiplos padrões para encontrar tweets
                padroes = [
                    r'class="tweet-content[^"]*"[^>]*>([^<]+)</div>',
                    r'<div class="tweet-content[^"]*">([^<]+)',
                    r'tweet-content.*?>([^<]{20,})</div>',
                    r'class="tweet-body".*?<div[^>]*>([^<]{20,})</div>'
                ]
                
                tweets_encontrados = []
                for padrao in padroes:
                    matches = re.findall(padrao, html, re.DOTALL)
                    tweets_encontrados.extend(matches)
                
                # Limpar HTML
                for tweet in tweets_encontrados:
                    texto = re.sub(r'<[^>]+>', '', tweet)
                    texto = re.sub(r'&\w+;', ' ', texto)
                    texto = texto.strip()
                    
                    if texto and len(texto) > 15 and texto not in posts:
                        posts.append(texto)
                
                if posts:
                    print(f"✓ {len(posts)} tweets")
                    break
                else:
                    print("✗")
            else:
                print(f"✗ ({response.status_code})")
        
        except Exception as e:
            print(f"✗ (erro)")
        
        time.sleep(0.5)  # Pausa entre tentativas
    
    # Se não encontrou, tentar busca genérica
    if not posts:
        print(f"\n   🔄 Tentando busca alternativa...")
        posts_busca = buscar_web_avancado(f"{username} twitter")
        posts.extend(posts_busca)
    
    return posts

def buscar_reddit_aprimorado(username):
    """Busca aprimorada no Reddit"""
    posts = []
    username = username.replace('@', '').strip()
    
    try:
        # Posts do usuário
        url = f"https://www.reddit.com/user/{username}/submitted.json?limit=100"
        headers = {"User-Agent": "Mozilla/5.0 (Research Bot v1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            for item in dados.get("data", {}).get("children", []):
                post = item.get("data", {})
                titulo = post.get("title", "")
                texto = post.get("selftext", "")
                conteudo = f"{titulo} {texto}".strip()
                
                if len(conteudo) > 20:
                    posts.append(conteudo)
        
        # Comentários do usuário
        url_comments = f"https://www.reddit.com/user/{username}/comments.json?limit=100"
        response = requests.get(url_comments, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            for item in dados.get("data", {}).get("children", []):
                comment = item.get("data", {})
                corpo = comment.get("body", "")
                if len(corpo) > 20:
                    posts.append(corpo)
    
    except Exception as e:
        pass
    
    return posts

def buscar_web_avancado(termo_busca):
    """Busca avançada na web usando múltiplas fontes"""
    posts = []
    
    # 1. DuckDuckGo
    try:
        url = "https://html.duckduckgo.com/html/"
        params = {"q": termo_busca}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.post(url, data=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            # Extrair resultados
            snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)', html)
            posts.extend([s.strip() for s in snippets if len(s.strip()) > 30])
    except:
        pass
    
    # 2. Bing (HTML público)
    try:
        url = f"https://www.bing.com/search"
        params = {"q": termo_busca}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            # Extrair snippets
            snippets = re.findall(r'class="b_caption"[^>]*>.*?<p>([^<]+)</p>', html, re.DOTALL)
            posts.extend([s.strip() for s in snippets if len(s.strip()) > 30])
    except:
        pass
    
    return posts

def buscar_google_news(termo):
    """Busca notícias no Google News"""
    posts = []
    
    try:
        url = f"https://news.google.com/rss/search"
        params = {"q": termo, "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            # Extrair títulos e descrições do RSS
            titulos = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', response.text)
            descricoes = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', response.text)
            
            posts.extend([t for t in titulos if len(t) > 20])
            posts.extend([d for d in descricoes if len(d) > 30])
    
    except:
        pass
    
    return posts

def buscar_youtube_aprimorado(username):
    """Busca aprimorada no YouTube"""
    posts = []
    username = username.replace('@', '').strip()
    
    # Tentar diferentes formatos de URL
    urls_tentar = [
        f"https://www.youtube.com/@{username}",
        f"https://www.youtube.com/c/{username}",
        f"https://www.youtube.com/user/{username}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    
    for url in urls_tentar:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Extrair descrição do canal
                match_desc = re.search(r'"description":"([^"]{50,})"', html)
                if match_desc:
                    posts.append(match_desc.group(1))
                
                # Extrair títulos de vídeos
                titulos = re.findall(r'"title":\{"runs":\[\{"text":"([^"]{20,})"\}\]\}', html)
                posts.extend(titulos[:20])
                
                if posts:
                    break
        except:
            continue
    
    return posts

def buscar_instagram_publico(username):
    """Tenta buscar dados públicos do Instagram"""
    posts = []
    username = username.replace('@', '').strip()
    
    try:
        # Página pública do Instagram
        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # Extrair bio
            match_bio = re.search(r'"biography":"([^"]+)"', html)
            if match_bio:
                posts.append(match_bio.group(1))
            
            # Extrair legendas de posts
            legendas = re.findall(r'"edge_media_to_caption".*?"text":"([^"]{30,})"', html)
            posts.extend(legendas[:15])
    
    except:
        pass
    
    return posts

# =========================
# ANÁLISE (mesma do anterior)
# =========================

def normalizar_texto(texto):
    """Remove acentos e normaliza"""
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

def analisar_textos(textos):
    """Analisa lista de textos"""
    if not textos:
        return None
    
    total_esq = 0
    total_dir = 0
    palavras_esq_encontradas = []
    palavras_dir_encontradas = []
    
    for texto in textos:
        texto_norm = normalizar_texto(texto)
        palavras = re.findall(r'\b\w+\b', texto_norm)
        
        for palavra in palavras:
            if palavra in PALAVRAS_ESQUERDA:
                total_esq += 1
                palavras_esq_encontradas.append(palavra)
            elif palavra in PALAVRAS_DIREITA:
                total_dir += 1
                palavras_dir_encontradas.append(palavra)
    
    total = total_esq + total_dir
    
    if total < 3:
        return {
            "classificacao": "INSUFICIENTE (poucos dados políticos)",
            "esquerda": 0,
            "direita": 0,
            "confianca": "MUITO BAIXA"
        }
    
    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    
    # Classificação
    diff = abs(pct_esq - pct_dir)
    
    if total < 10:
        confianca = "BAIXA"
    elif total < 25:
        confianca = "MÉDIA"
    else:
        confianca = "ALTA"
    
    if diff < 15:
        classe = "CENTRO (equilibrado)"
    elif diff < 35:
        classe = "CENTRO-ESQUERDA" if pct_esq > pct_dir else "CENTRO-DIREITA"
    else:
        classe = "ESQUERDA" if pct_esq > pct_dir else "DIREITA"
    
    # Palavras mais comuns
    top_esq = Counter(palavras_esq_encontradas).most_common(5)
    top_dir = Counter(palavras_dir_encontradas).most_common(5)
    
    return {
        "classificacao": classe,
        "esquerda": round(pct_esq, 1),
        "direita": round(pct_dir, 1),
        "confianca": confianca,
        "textos_analisados": len(textos),
        "pontos_esq": total_esq,
        "pontos_dir": total_dir,
        "top_palavras_esq": top_esq,
        "top_palavras_dir": top_dir
    }

# =========================
# BUSCA PROFUNDA
# =========================

def buscar_profundo(username):
    """Busca PROFUNDA em todas as plataformas"""
    
    # Limpar username
    username_limpo = username.replace('@', '').strip()
    
    print(f"\n{'='*80}")
    print(f"🔍 BUSCA PROFUNDA: {username_limpo}")
    print(f"{'='*80}")
    print("⏳ Isso pode levar alguns minutos...")
    
    todas_postagens = []
    plataformas_encontradas = []
    
    # 1. TWITTER/X - Prioridade máxima
    print(f"\n🐦 TWITTER/X")
    posts_twitter = buscar_twitter_multiplas_fontes(username_limpo)
    if posts_twitter:
        todas_postagens.extend(posts_twitter)
        plataformas_encontradas.append(f"Twitter/X ({len(posts_twitter)})")
        print(f"   ✓ Total: {len(posts_twitter)} tweets")
    else:
        print(f"   ✗ Nenhum tweet encontrado")
    
    # 2. INSTAGRAM
    print(f"\n📷 INSTAGRAM")
    print(f"   Buscando @{username_limpo}...", end=" ", flush=True)
    posts_insta = buscar_instagram_publico(username_limpo)
    if posts_insta:
        todas_postagens.extend(posts_insta)
        plataformas_encontradas.append(f"Instagram ({len(posts_insta)})")
        print(f"✓ {len(posts_insta)} posts")
    else:
        print("✗")
    
    # 3. YOUTUBE
    print(f"\n🎥 YOUTUBE")
    print(f"   Buscando canal...", end=" ", flush=True)
    posts_youtube = buscar_youtube_aprimorado(username_limpo)
    if posts_youtube:
        todas_postagens.extend(posts_youtube)
        plataformas_encontradas.append(f"YouTube ({len(posts_youtube)})")
        print(f"✓ {len(posts_youtube)} itens")
    else:
        print("✗")
    
    # 4. REDDIT
    print(f"\n📱 REDDIT")
    print(f"   Buscando u/{username_limpo}...", end=" ", flush=True)
    posts_reddit = buscar_reddit_aprimorado(username_limpo)
    if posts_reddit:
        todas_postagens.extend(posts_reddit)
        plataformas_encontradas.append(f"Reddit ({len(posts_reddit)})")
        print(f"✓ {len(posts_reddit)} posts")
    else:
        print("✗")
    
    # 5. GOOGLE NEWS
    print(f"\n📰 GOOGLE NEWS")
    print(f"   Buscando notícias...", end=" ", flush=True)
    posts_news = buscar_google_news(username_limpo)
    if posts_news:
        todas_postagens.extend(posts_news)
        plataformas_encontradas.append(f"Google News ({len(posts_news)})")
        print(f"✓ {len(posts_news)} notícias")
    else:
        print("✗")
    
    # 6. BUSCA WEB GERAL
    print(f"\n🌐 BUSCA WEB GERAL")
    print(f"   Buscando menções...", end=" ", flush=True)
    posts_web = buscar_web_avancado(f"{username_limpo} política brasil")
    if posts_web:
        todas_postagens.extend(posts_web)
        plataformas_encontradas.append(f"Web ({len(posts_web)})")
        print(f"✓ {len(posts_web)} menções")
    else:
        print("✗")
    
    # RESULTADO FINAL
    print(f"\n{'='*80}")
    
    if not todas_postagens:
        print("❌ NENHUM DADO ENCONTRADO")
        print(f"\n💡 Sugestões:")
        print(f"   • Verifique a ortografia do username")
        print(f"   • Tente sem '@' ou outros caracteres especiais")
        print(f"   • Alguns perfis podem estar privados ou bloqueados")
        print(f"   • Experimente variações: com/sem números, maiúsculas, etc")
        return None
    
    print(f"✅ COLETA CONCLUÍDA!")
    print(f"   📊 Total: {len(todas_postagens)} textos")
    print(f"   🌐 Plataformas: {len(plataformas_encontradas)}")
    for plat in plataformas_encontradas:
        print(f"      • {plat}")
    
    # ANÁLISE
    print(f"\n📊 Analisando conteúdo...")
    resultado = analisar_textos(todas_postagens)
    
    if resultado:
        resultado["plataformas"] = plataformas_encontradas
        resultado["username"] = username_limpo
        resultado["total_textos"] = len(todas_postagens)
        exibir_resultado(resultado)
        salvar_resultado(resultado)
    
    return resultado

def exibir_resultado(res):
    """Exibe resultado formatado"""
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO DA ANÁLISE")
    print(f"{'='*80}")
    
    print(f"\n👤 Username: {res['username']}")
    print(f"🎯 Classificação: {res['classificacao']}")
    print(f"📈 Confiança: {res['confianca']}")
    
    print(f"\n📊 DISTRIBUIÇÃO:")
    barra_esq = "█" * int(res['esquerda'] / 2)
    barra_dir = "█" * int(res['direita'] / 2)
    print(f"  🔴 Esquerda: {res['esquerda']:>5.1f}% {barra_esq}")
    print(f"  🔵 Direita:  {res['direita']:>5.1f}% {barra_dir}")
    
    print(f"\n📝 DETALHES DA COLETA:")
    print(f"  • Total de textos: {res.get('total_textos', 0)}")
    print(f"  • Textos com conteúdo político: {res['textos_analisados']}")
    print(f"  • Pontos esquerda: {res['pontos_esq']}")
    print(f"  • Pontos direita: {res['pontos_dir']}")
    print(f"  • Plataformas encontradas: {len(res['plataformas'])}")
    
    if res['top_palavras_esq']:
        print(f"\n🔴 Top 5 palavras ESQUERDA:")
        for palavra, freq in res['top_palavras_esq']:
            print(f"     • {palavra}: {freq}x")
    
    if res['top_palavras_dir']:
        print(f"\n🔵 Top 5 palavras DIREITA:")
        for palavra, freq in res['top_palavras_dir']:
            print(f"     • {palavra}: {freq}x")
    
    print(f"\n{'='*80}")

def salvar_resultado(resultado):
    """Salva resultado detalhado"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analise_{resultado['username']}_{timestamp}.json"
    
    resultado['data_analise'] = datetime.now().isoformat()
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Resultado salvo: {filename}")

# =========================
# MENU
# =========================

def menu():
    """Menu principal"""
    while True:
        print(f"\n{'='*80}")
        print("🎯 ANÁLISE POLÍTICA PROFUNDA")
        print(f"{'='*80}")
        print("\n1. 🔍 Buscar username (BUSCA PROFUNDA)")
        print("2. ℹ️  Informações do sistema")
        print("3. 🚪 Sair")
        
        try:
            opcao = input("\nEscolha (1-3): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Até logo!")
            break
        
        if opcao == "1":
            try:
                username = input("\n👤 Digite o username: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Cancelado")
                continue
            
            if username:
                buscar_profundo(username)
            else:
                print("❌ Username inválido!")
            
            input("\nPressione Enter para continuar...")
        
        elif opcao == "2":
            print(f"\n{'='*80}")
            print("ℹ️  INFORMAÇÕES DO SISTEMA")
            print(f"{'='*80}")
            print("\n📋 BUSCA PROFUNDA INCLUI:")
            print("   • Twitter/X - Múltiplas instâncias Nitter")
            print("   • Instagram - Perfil público e posts")
            print("   • YouTube - Canal, descrição e vídeos")
            print("   • Reddit - Posts e comentários")
            print("   • Google News - Notícias relacionadas")
            print("   • Busca Web - DuckDuckGo e Bing")
            print("\n📊 ANÁLISE:")
            print("   • Baseada em +100 palavras-chave políticas")
            print("   • Classifica: Esquerda / Centro / Direita")
            print("   • Confiabilidade baseada em volume de dados")
            print("\n⚙️  RECURSOS:")
            print("   • Múltiplas tentativas por plataforma")
            print("   • Fallback automático se uma fonte falhar")
            print("   • Salvamento automático em JSON")
            print("\n⏱️  TEMPO ESTIMADO:")
            print("   • 1-3 minutos por username")
            print(f"\n{'='*80}")
            input("\nPressione Enter para continuar...")
        
        elif opcao == "3":
            print("\n👋 Até logo!")
            break

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print("ANÁLISE POLÍTICA PROFUNDA")
    print("Versão 4.0 - Busca Intensiva Multi-Plataformas")
    print(f"{'='*80}")
    print("\n⚠️  AVISO:")
    print("   • Busca APENAS dados públicos")
    print("   • Pode levar alguns minutos")
    print("   • Use para fins educacionais")
    print(f"{'='*80}")
    
    menu()