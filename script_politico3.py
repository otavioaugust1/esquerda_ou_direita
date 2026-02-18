"""
ANÁLISE POLÍTICA SIMPLIFICADA - BUSCA EM MÚLTIPLAS REDES SOCIAIS
Versão 3.0 - Simples e Direto
"""

import requests
import re
import json
from datetime import datetime
from collections import Counter

# =========================
# PALAVRAS-CHAVE
# =========================
PALAVRAS_ESQUERDA = {
    "democracia", "democratico", "direitos", "humanos", "justica",
    "social", "igualdade", "trabalhador", "sus", "saude", "publica",
    "educacao", "federal", "feminismo", "lgbt", "diversidade",
    "ambiente", "amazonia", "indigena", "fascismo", "neoliberalismo",
    "pt", "psol", "lula", "dilma", "marielle"
}

PALAVRAS_DIREITA = {
    "liberdade", "economica", "livre", "mercado", "capitalismo",
    "empreendedor", "privatizacao", "minimo", "meritocracia",
    "imposto", "tributo", "familia", "tradicional", "cristaos",
    "deus", "conservador", "patriota", "seguranca", "ordem",
    "armas", "comunismo", "socialismo", "corrupcao", "petismo",
    "bolsonaro", "mito"
}

# =========================
# FUNÇÕES DE BUSCA POR PLATAFORMA
# =========================

def buscar_reddit(username):
    """Busca posts no Reddit"""
    posts = []
    try:
        url = f"https://www.reddit.com/user/{username}/submitted.json?limit=50"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            for item in dados.get("data", {}).get("children", []):
                post = item.get("data", {})
                texto = f"{post.get('title', '')} {post.get('selftext', '')}"
                if len(texto.strip()) > 20:
                    posts.append(texto)
    except:
        pass
    
    return posts

def buscar_github(username):
    """Busca bio e repos no GitHub"""
    posts = []
    try:
        # Perfil
        url = f"https://api.github.com/users/{username}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            bio = dados.get("bio", "")
            if bio:
                posts.append(bio)
            
            # Repos
            url_repos = f"https://api.github.com/users/{username}/repos?per_page=20"
            response = requests.get(url_repos, timeout=10)
            if response.status_code == 200:
                repos = response.json()
                for repo in repos:
                    desc = repo.get("description", "")
                    if desc:
                        posts.append(desc)
    except:
        pass
    
    return posts

def buscar_twitter_via_nitter(username):
    """Tenta buscar via Nitter (mirror do Twitter/X)"""
    posts = []
    instancias = [
        "nitter.poast.org",
        "nitter.privacydev.net",
        "nitter.net"
    ]
    
    for instancia in instancias:
        try:
            url = f"https://{instancia}/{username}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                # Buscar conteúdo de tweets
                tweets = re.findall(r'class="tweet-content[^"]*"[^>]*>([^<]+)', html)
                posts.extend([t.strip() for t in tweets if len(t.strip()) > 20])
                
                if posts:
                    break
        except:
            continue
    
    return posts

def buscar_web_geral(username):
    """Busca menções do username na web via DuckDuckGo"""
    posts = []
    try:
        # DuckDuckGo HTML (sem API key necessária)
        url = "https://html.duckduckgo.com/html/"
        params = {"q": f"{username} politics brasil"}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.post(url, data=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            # Extrair snippets de resultados
            resultados = re.findall(r'class="result__snippet"[^>]*>([^<]+)', html)
            posts.extend([r.strip() for r in resultados if len(r.strip()) > 30])
    except:
        pass
    
    return posts

def buscar_youtube_scraping(username):
    """Tenta buscar via scraping simples do YouTube"""
    posts = []
    try:
        # Buscar canal
        url = f"https://www.youtube.com/@{username}/about"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            # Tentar extrair descrição do canal
            match = re.search(r'"description":\{"simpleText":"([^"]+)"', html)
            if match:
                posts.append(match.group(1))
    except:
        pass
    
    return posts

# =========================
# ANÁLISE
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
    
    if total == 0:
        return {
            "classificacao": "NEUTRO/SEM DADOS",
            "esquerda": 0,
            "direita": 0,
            "confianca": "BAIXA"
        }
    
    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    
    # Classificação
    diff = abs(pct_esq - pct_dir)
    
    if diff < 15:
        classe = "CENTRO (equilibrado)"
        confianca = "MÉDIA"
    elif diff < 35:
        if pct_esq > pct_dir:
            classe = "CENTRO-ESQUERDA"
        else:
            classe = "CENTRO-DIREITA"
        confianca = "MÉDIA"
    else:
        if pct_esq > pct_dir:
            classe = "ESQUERDA"
        else:
            classe = "DIREITA"
        confianca = "ALTA"
    
    # Palavras mais comuns
    top_esq = Counter(palavras_esq_encontradas).most_common(3)
    top_dir = Counter(palavras_dir_encontradas).most_common(3)
    
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
# BUSCA MULTI-PLATAFORMA
# =========================

def buscar_todas_plataformas(username):
    """Busca em todas as plataformas automaticamente"""
    
    print(f"\n{'='*80}")
    print(f"🔍 BUSCANDO: @{username}")
    print(f"{'='*80}")
    
    todas_postagens = []
    plataformas_encontradas = []
    
    # 1. REDDIT
    print("\n📱 Reddit...", end=" ")
    posts_reddit = buscar_reddit(username)
    if posts_reddit:
        todas_postagens.extend(posts_reddit)
        plataformas_encontradas.append(f"Reddit ({len(posts_reddit)} posts)")
        print(f"✓ {len(posts_reddit)} posts")
    else:
        print("✗")
    
    # 2. GITHUB
    print("💻 GitHub...", end=" ")
    posts_github = buscar_github(username)
    if posts_github:
        todas_postagens.extend(posts_github)
        plataformas_encontradas.append(f"GitHub ({len(posts_github)} itens)")
        print(f"✓ {len(posts_github)} itens")
    else:
        print("✗")
    
    # 3. TWITTER/X via Nitter
    print("🐦 Twitter/X (via Nitter)...", end=" ")
    posts_twitter = buscar_twitter_via_nitter(username)
    if posts_twitter:
        todas_postagens.extend(posts_twitter)
        plataformas_encontradas.append(f"Twitter/X ({len(posts_twitter)} tweets)")
        print(f"✓ {len(posts_twitter)} tweets")
    else:
        print("✗")
    
    # 4. YOUTUBE
    print("🎥 YouTube...", end=" ")
    posts_youtube = buscar_youtube_scraping(username)
    if posts_youtube:
        todas_postagens.extend(posts_youtube)
        plataformas_encontradas.append(f"YouTube ({len(posts_youtube)} itens)")
        print(f"✓ {len(posts_youtube)} itens")
    else:
        print("✗")
    
    # 5. WEB GERAL
    print("🌐 Web Geral (DuckDuckGo)...", end=" ")
    posts_web = buscar_web_geral(username)
    if posts_web:
        todas_postagens.extend(posts_web)
        plataformas_encontradas.append(f"Web ({len(posts_web)} menções)")
        print(f"✓ {len(posts_web)} menções")
    else:
        print("✗")
    
    # RESULTADO
    print(f"\n{'='*80}")
    
    if not todas_postagens:
        print("❌ NENHUM DADO ENCONTRADO")
        print(f"\n💡 Dicas:")
        print(f"   • Verifique se o username está correto")
        print(f"   • Alguns perfis podem ser privados ou inexistentes")
        print(f"   • Tente variações do nome (com/sem números, etc)")
        return None
    
    print(f"✓ TOTAL: {len(todas_postagens)} textos coletados")
    print(f"📍 Plataformas: {', '.join(plataformas_encontradas)}")
    
    # ANÁLISE
    print(f"\n📊 Analisando conteúdo...")
    resultado = analisar_textos(todas_postagens)
    
    if resultado:
        resultado["plataformas"] = plataformas_encontradas
        resultado["username"] = username
        exibir_resultado(resultado)
        
        # Salvar
        salvar_resultado(resultado)
    
    return resultado

def exibir_resultado(res):
    """Exibe resultado formatado"""
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO DA ANÁLISE")
    print(f"{'='*80}")
    
    print(f"\n👤 Username: @{res['username']}")
    print(f"🎯 Classificação: {res['classificacao']}")
    print(f"📈 Confiança: {res['confianca']}")
    
    print(f"\n📊 DISTRIBUIÇÃO:")
    barra_esq = "█" * int(res['esquerda'] / 2)
    barra_dir = "█" * int(res['direita'] / 2)
    print(f"  🔴 Esquerda: {res['esquerda']:>5.1f}% {barra_esq}")
    print(f"  🔵 Direita:  {res['direita']:>5.1f}% {barra_dir}")
    
    print(f"\n📝 DETALHES:")
    print(f"  • Textos analisados: {res['textos_analisados']}")
    print(f"  • Pontos esquerda: {res['pontos_esq']}")
    print(f"  • Pontos direita: {res['pontos_dir']}")
    print(f"  • Plataformas: {len(res['plataformas'])}")
    
    if res['top_palavras_esq']:
        print(f"\n🔴 Top palavras ESQUERDA:")
        for palavra, freq in res['top_palavras_esq']:
            print(f"     • {palavra}: {freq}x")
    
    if res['top_palavras_dir']:
        print(f"\n🔵 Top palavras DIREITA:")
        for palavra, freq in res['top_palavras_dir']:
            print(f"     • {palavra}: {freq}x")
    
    print(f"\n{'='*80}")

def salvar_resultado(resultado):
    """Salva resultado em JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analise_{resultado['username']}_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Resultado salvo: {filename}")

# =========================
# MENU PRINCIPAL
# =========================

def menu():
    """Menu simplificado"""
    while True:
        print(f"\n{'='*80}")
        print("🎯 ANÁLISE POLÍTICA - MULTI PLATAFORMAS")
        print(f"{'='*80}")
        print("\n1. 🔍 Analisar username")
        print("2. ℹ️  Informações")
        print("3. 🚪 Sair")
        
        try:
            opcao = input("\nEscolha (1-3): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Até logo!")
            break
        
        if opcao == "1":
            try:
                username = input("\n👤 Digite o username (sem @): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Cancelado")
                continue
            
            if username:
                buscar_todas_plataformas(username)
            else:
                print("❌ Username inválido!")
            
            input("\nPressione Enter para continuar...")
        
        elif opcao == "2":
            print(f"\n{'='*80}")
            print("ℹ️  INFORMAÇÕES")
            print(f"{'='*80}")
            print("\n📋 O QUE FAZ:")
            print("   Busca automaticamente em múltiplas redes sociais")
            print("   e analisa o conteúdo para identificar tendência política")
            print("\n🌐 PLATAFORMAS SUPORTADAS:")
            print("   • Reddit - Posts públicos")
            print("   • GitHub - Bio e repositórios")
            print("   • Twitter/X - Via Nitter (mirror público)")
            print("   • YouTube - Descrição de canal")
            print("   • Web Geral - Buscas no DuckDuckGo")
            print("\n⚖️  METODOLOGIA:")
            print("   • Análise por palavras-chave")
            print("   • Classificação: Esquerda / Centro / Direita")
            print("   • Confiança baseada em quantidade de dados")
            print("\n⚠️  LIMITAÇÕES:")
            print("   • Depende de dados públicos disponíveis")
            print("   • Alguns perfis podem ser privados")
            print("   • Análise é indicativa, não definitiva")
            print(f"\n{'='*80}")
            input("\nPressione Enter para continuar...")
        
        elif opcao == "3":
            print("\n👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida!")

# =========================
# EXECUÇÃO
# =========================

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print("ANÁLISE POLÍTICA SIMPLIFICADA")
    print("Versão 3.0 - Multi Plataformas")
    print(f"{'='*80}")
    print("\n⚠️  Este programa analisa apenas dados PÚBLICOS")
    print("   Use para fins educacionais e de pesquisa")
    print(f"{'='*80}")
    
    menu()