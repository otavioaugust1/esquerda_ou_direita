"""
ANÁLISE POLÍTICA - DADOS REAIS DE APIs OFICIAIS
Versão 5.0 - Apenas dados REALMENTE verificáveis
"""

import requests
import re
import json
from datetime import datetime
from collections import Counter
import time

# =========================
# CONFIGURAÇÕES
# =========================

# Palavras-chave
PALAVRAS_ESQUERDA = {
    "democracia", "democratico", "direitos", "humanos", "justica",
    "social", "igualdade", "trabalhador", "sus", "saude", "publica",
    "educacao", "federal", "feminismo", "lgbt", "diversidade",
    "ambiente", "amazonia", "indigena", "fascismo", "neoliberalismo",
    "pt", "psol", "lula", "dilma", "marielle", "redistribuicao"
}

PALAVRAS_DIREITA = {
    "liberdade", "economica", "livre", "mercado", "capitalismo",
    "empreendedor", "privatizacao", "meritocracia", "imposto",
    "familia", "tradicional", "cristaos", "deus", "conservador",
    "patriota", "seguranca", "ordem", "armas", "comunismo",
    "bolsonaro", "mito", "corrupcao", "petismo"
}

# =========================
# FUNÇÕES DE BUSCA - APENAS DADOS REAIS
# =========================

def verificar_reddit_existe(username):
    """Verifica se o usuário existe no Reddit"""
    try:
        url = f"https://www.reddit.com/user/{username}/about.json"
        headers = {"User-Agent": "Mozilla/5.0 (Research Bot)"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("data"):
                return True
        return False
    except:
        return False

def buscar_reddit_real(username):
    """Busca REAL no Reddit - apenas se o usuário existir"""
    print(f"\n📱 REDDIT")
    print(f"   Verificando se u/{username} existe...", end=" ", flush=True)
    
    if not verificar_reddit_existe(username):
        print("✗ (usuário não encontrado)")
        return []
    
    print("✓")
    
    posts = []
    
    try:
        # Posts
        print(f"   Coletando posts...", end=" ", flush=True)
        url = f"https://www.reddit.com/user/{username}/submitted.json?limit=100"
        headers = {"User-Agent": "Mozilla/5.0 (Research Bot)"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            for item in dados.get("data", {}).get("children", []):
                post = item.get("data", {})
                titulo = post.get("title", "")
                texto = post.get("selftext", "")
                conteudo = f"{titulo} {texto}".strip()
                
                if len(conteudo) > 20:
                    posts.append({
                        "texto": conteudo,
                        "fonte": "Reddit - Post",
                        "url": f"https://reddit.com{post.get('permalink', '')}"
                    })
            print(f"✓ {len(posts)} posts")
        else:
            print("✗")
        
        # Comentários
        print(f"   Coletando comentários...", end=" ", flush=True)
        url_comments = f"https://www.reddit.com/user/{username}/comments.json?limit=100"
        response = requests.get(url_comments, headers=headers, timeout=10)
        
        comentarios_count = 0
        if response.status_code == 200:
            dados = response.json()
            for item in dados.get("data", {}).get("children", []):
                comment = item.get("data", {})
                corpo = comment.get("body", "")
                if len(corpo) > 20:
                    posts.append({
                        "texto": corpo,
                        "fonte": "Reddit - Comentário",
                        "url": f"https://reddit.com{comment.get('permalink', '')}"
                    })
                    comentarios_count += 1
            print(f"✓ {comentarios_count} comentários")
        else:
            print("✗")
    
    except Exception as e:
        print(f"✗ (erro: {str(e)[:30]})")
    
    return posts

def buscar_github_real(username):
    """Busca REAL no GitHub"""
    print(f"\n💻 GITHUB")
    print(f"   Verificando usuário {username}...", end=" ", flush=True)
    
    posts = []
    
    try:
        # Perfil
        url = f"https://api.github.com/users/{username}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            print("✗ (usuário não encontrado)")
            return []
        
        if response.status_code != 200:
            print(f"✗ (erro {response.status_code})")
            return []
        
        print("✓")
        
        dados = response.json()
        
        # Bio
        bio = dados.get("bio")
        if bio and len(bio) > 10:
            posts.append({
                "texto": bio,
                "fonte": "GitHub - Bio",
                "url": dados.get("html_url")
            })
            print(f"   Bio: ✓")
        
        # Repositórios
        print(f"   Coletando repositórios...", end=" ", flush=True)
        url_repos = f"https://api.github.com/users/{username}/repos?per_page=50&sort=updated"
        response = requests.get(url_repos, headers=headers, timeout=10)
        
        repos_count = 0
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                desc = repo.get("description")
                if desc and len(desc) > 10:
                    posts.append({
                        "texto": desc,
                        "fonte": f"GitHub - Repo: {repo.get('name')}",
                        "url": repo.get("html_url")
                    })
                    repos_count += 1
            print(f"✓ {repos_count} repos com descrição")
        else:
            print("✗")
    
    except Exception as e:
        print(f"✗ (erro: {str(e)[:30]})")
    
    return posts

def buscar_mastodon_real(username, instancia="mastodon.social"):
    """Busca REAL no Mastodon"""
    print(f"\n🐘 MASTODON")
    print(f"   Verificando @{username}@{instancia}...", end=" ", flush=True)
    
    posts = []
    
    try:
        # Buscar usuário
        url = f"https://{instancia}/api/v1/accounts/lookup"
        params = {"acct": username}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            print("✗ (usuário não encontrado)")
            return []
        
        if response.status_code != 200:
            print(f"✗ (erro {response.status_code})")
            return []
        
        print("✓")
        
        user_data = response.json()
        user_id = user_data.get("id")
        
        # Posts
        print(f"   Coletando posts...", end=" ", flush=True)
        url_posts = f"https://{instancia}/api/v1/accounts/{user_id}/statuses"
        params = {"limit": 40, "exclude_replies": False}
        response = requests.get(url_posts, params=params, timeout=10)
        
        if response.status_code == 200:
            posts_data = response.json()
            for post in posts_data:
                # Remover HTML
                texto = re.sub(r'<[^>]+>', '', post.get("content", ""))
                if len(texto) > 20:
                    posts.append({
                        "texto": texto,
                        "fonte": "Mastodon",
                        "url": post.get("url")
                    })
            print(f"✓ {len(posts)} posts")
        else:
            print("✗")
    
    except Exception as e:
        print(f"✗ (erro: {str(e)[:30]})")
    
    return posts

def buscar_hackernews_real(username):
    """Busca REAL no Hacker News"""
    print(f"\n🔶 HACKER NEWS")
    print(f"   Verificando usuário {username}...", end=" ", flush=True)
    
    posts = []
    
    try:
        # Verificar se usuário existe
        url = f"https://hacker-news.firebaseio.com/v0/user/{username}.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200 or not response.text or response.text == "null":
            print("✗ (usuário não encontrado)")
            return []
        
        print("✓")
        
        user_data = response.json()
        submitted_ids = user_data.get("submitted", [])
        
        print(f"   Coletando posts (até 30)...", end=" ", flush=True)
        
        count = 0
        for item_id in submitted_ids[:30]:
            try:
                url_item = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                response = requests.get(url_item, timeout=5)
                
                if response.status_code == 200:
                    item = response.json()
                    
                    # Pegar título ou texto
                    texto = item.get("title", "") or item.get("text", "")
                    
                    if texto and len(texto) > 20:
                        posts.append({
                            "texto": re.sub(r'<[^>]+>', '', texto),
                            "fonte": "Hacker News",
                            "url": f"https://news.ycombinator.com/item?id={item_id}"
                        })
                        count += 1
                
                time.sleep(0.1)  # Rate limiting
            except:
                continue
        
        print(f"✓ {count} itens")
    
    except Exception as e:
        print(f"✗ (erro: {str(e)[:30]})")
    
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
    """Analisa posts coletados"""
    if not posts:
        return None
    
    total_esq = 0
    total_dir = 0
    palavras_esq = []
    palavras_dir = []
    posts_com_conteudo_politico = []
    
    for post in posts:
        texto = post.get("texto", "")
        texto_norm = normalizar_texto(texto)
        palavras = re.findall(r'\b\w+\b', texto_norm)
        
        pontos_post_esq = 0
        pontos_post_dir = 0
        
        for palavra in palavras:
            if palavra in PALAVRAS_ESQUERDA:
                total_esq += 1
                palavras_esq.append(palavra)
                pontos_post_esq += 1
            elif palavra in PALAVRAS_DIREITA:
                total_dir += 1
                palavras_dir.append(palavra)
                pontos_post_dir += 1
        
        # Se tem conteúdo político
        if pontos_post_esq > 0 or pontos_post_dir > 0:
            posts_com_conteudo_politico.append({
                **post,
                "pontos_esq": pontos_post_esq,
                "pontos_dir": pontos_post_dir
            })
    
    total = total_esq + total_dir
    
    if total < 3:
        return {
            "classificacao": "SEM CONTEÚDO POLÍTICO DETECTADO",
            "esquerda": 0,
            "direita": 0,
            "confianca": "NENHUMA",
            "total_posts": len(posts),
            "posts_politicos": 0
        }
    
    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    
    # Classificação
    diff = abs(pct_esq - pct_dir)
    
    if total < 5:
        confianca = "MUITO BAIXA"
    elif total < 15:
        confianca = "BAIXA"
    elif total < 30:
        confianca = "MÉDIA"
    else:
        confianca = "ALTA"
    
    if diff < 10:
        classe = "CENTRO (muito equilibrado)"
    elif diff < 25:
        classe = "CENTRO-ESQUERDA" if pct_esq > pct_dir else "CENTRO-DIREITA"
    else:
        classe = "ESQUERDA" if pct_esq > pct_dir else "DIREITA"
    
    return {
        "classificacao": classe,
        "esquerda": round(pct_esq, 1),
        "direita": round(pct_dir, 1),
        "confianca": confianca,
        "total_posts": len(posts),
        "posts_politicos": len(posts_com_conteudo_politico),
        "pontos_esq": total_esq,
        "pontos_dir": total_dir,
        "top_palavras_esq": Counter(palavras_esq).most_common(5),
        "top_palavras_dir": Counter(palavras_dir).most_common(5),
        "exemplos_posts": posts_com_conteudo_politico[:3]
    }

# =========================
# BUSCA PRINCIPAL
# =========================

def analisar_usuario(username):
    """Análise completa de um usuário"""
    
    username = username.replace('@', '').strip()
    
    print(f"\n{'='*80}")
    print(f"🔍 ANÁLISE: {username}")
    print(f"{'='*80}")
    print("⏳ Buscando em plataformas com APIs públicas...")
    print("   (Apenas dados reais e verificáveis)")
    
    todos_posts = []
    plataformas_sucesso = []
    
    # Reddit
    posts_reddit = buscar_reddit_real(username)
    if posts_reddit:
        todos_posts.extend(posts_reddit)
        plataformas_sucesso.append(f"Reddit ({len(posts_reddit)})")
    
    time.sleep(1)
    
    # GitHub
    posts_github = buscar_github_real(username)
    if posts_github:
        todos_posts.extend(posts_github)
        plataformas_sucesso.append(f"GitHub ({len(posts_github)})")
    
    time.sleep(1)
    
    # Hacker News
    posts_hn = buscar_hackernews_real(username)
    if posts_hn:
        todos_posts.extend(posts_hn)
        plataformas_sucesso.append(f"Hacker News ({len(posts_hn)})")
    
    time.sleep(1)
    
    # Mastodon (opcional)
    resposta_mastodon = input(f"\n🐘 Tentar Mastodon? (Digite a instância ou Enter para pular): ").strip()
    if resposta_mastodon:
        posts_mastodon = buscar_mastodon_real(username, resposta_mastodon)
        if posts_mastodon:
            todos_posts.extend(posts_mastodon)
            plataformas_sucesso.append(f"Mastodon ({len(posts_mastodon)})")
    
    # Resultado
    print(f"\n{'='*80}")
    print(f"📊 COLETA FINALIZADA")
    print(f"{'='*80}")
    
    if not todos_posts:
        print("❌ NENHUM DADO ENCONTRADO")
        print(f"\n💡 Possíveis razões:")
        print(f"   • Username não existe nessas plataformas")
        print(f"   • Perfis estão vazios ou privados")
        print(f"   • Tente outras variações do username")
        return None
    
    print(f"✅ Total: {len(todos_posts)} posts/itens coletados")
    print(f"🌐 Plataformas com dados: {len(plataformas_sucesso)}")
    for plat in plataformas_sucesso:
        print(f"   • {plat}")
    
    # Análise
    print(f"\n📊 Analisando conteúdo...")
    resultado = analisar_posts(todos_posts)
    
    if resultado:
        resultado["username"] = username
        resultado["plataformas"] = plataformas_sucesso
        resultado["data_analise"] = datetime.now().isoformat()
        
        exibir_resultado(resultado)
        salvar_resultado(resultado, todos_posts)
    
    return resultado

def exibir_resultado(res):
    """Exibe resultado"""
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO")
    print(f"{'='*80}")
    
    print(f"\n👤 Username: {res['username']}")
    print(f"🎯 Classificação: {res['classificacao']}")
    print(f"📈 Confiança: {res['confianca']}")
    
    if res['confianca'] != "NENHUMA":
        print(f"\n📊 DISTRIBUIÇÃO:")
        barra_esq = "█" * int(res['esquerda'] / 2)
        barra_dir = "█" * int(res['direita'] / 2)
        print(f"  🔴 Esquerda: {res['esquerda']:>5.1f}% {barra_esq}")
        print(f"  🔵 Direita:  {res['direita']:>5.1f}% {barra_dir}")
    
    print(f"\n📝 DADOS COLETADOS:")
    print(f"  • Total de posts/itens: {res['total_posts']}")
    print(f"  • Com conteúdo político: {res['posts_politicos']}")
    
    if res.get('pontos_esq'):
        print(f"  • Pontos esquerda: {res['pontos_esq']}")
    if res.get('pontos_dir'):
        print(f"  • Pontos direita: {res['pontos_dir']}")
    
    if res.get('top_palavras_esq'):
        print(f"\n🔴 Palavras-chave ESQUERDA:")
        for palavra, freq in res['top_palavras_esq']:
            print(f"     • {palavra}: {freq}x")
    
    if res.get('top_palavras_dir'):
        print(f"\n🔵 Palavras-chave DIREITA:")
        for palavra, freq in res['top_palavras_dir']:
            print(f"     • {palavra}: {freq}x")
    
    if res.get('exemplos_posts'):
        print(f"\n📄 EXEMPLOS DE POSTS COM CONTEÚDO POLÍTICO:")
        for i, post in enumerate(res['exemplos_posts'], 1):
            print(f"\n   {i}. {post['fonte']}")
            print(f"      Texto: {post['texto'][:100]}...")
            print(f"      URL: {post.get('url', 'N/A')}")
    
    print(f"\n{'='*80}")

def salvar_resultado(resultado, posts):
    """Salva resultado completo"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analise_{resultado['username']}_{timestamp}.json"
    
    dados_completos = {
        **resultado,
        "posts_completos": posts
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(dados_completos, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Resultado salvo: {filename}")

# =========================
# MENU
# =========================

def menu():
    """Menu principal"""
    while True:
        print(f"\n{'='*80}")
        print("🎯 ANÁLISE POLÍTICA - DADOS REAIS")
        print(f"{'='*80}")
        print("\n1. 🔍 Analisar username")
        print("2. ℹ️  Sobre as fontes de dados")
        print("3. 🚪 Sair")
        
        try:
            opcao = input("\nEscolha (1-3): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Até logo!")
            break
        
        if opcao == "1":
            try:
                username = input("\n👤 Username: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Cancelado")
                continue
            
            if username:
                analisar_usuario(username)
            else:
                print("❌ Username inválido!")
            
            input("\nPressione Enter para continuar...")
        
        elif opcao == "2":
            print(f"\n{'='*80}")
            print("ℹ️  FONTES DE DADOS")
            print(f"{'='*80}")
            print("\n✅ PLATAFORMAS COM APIs PÚBLICAS REAIS:")
            print("   • Reddit - API oficial, sem autenticação")
            print("   • GitHub - API oficial REST v3")
            print("   • Hacker News - Firebase API oficial")
            print("   • Mastodon - API oficial ActivityPub")
            print("\n🔍 O QUE É COLETADO:")
            print("   • Reddit: Posts e comentários públicos")
            print("   • GitHub: Bio e descrições de repositórios")
            print("   • Hacker News: Posts e comentários")
            print("   • Mastodon: Posts públicos (toots)")
            print("\n⚠️  LIMITAÇÕES:")
            print("   • Twitter/X não tem API gratuita real")
            print("   • Instagram/Facebook não permitem scraping")
            print("   • TikTok não tem API pública")
            print("\n✅ GARANTIAS:")
            print("   • 100% dados reais e verificáveis")
            print("   • URLs de cada post são fornecidas")
            print("   • Você pode conferir manualmente cada dado")
            print(f"\n{'='*80}")
            input("\nPressione Enter...")
        
        elif opcao == "3":
            print("\n👋 Até logo!")
            break

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print("ANÁLISE POLÍTICA - APENAS DADOS REAIS")
    print("Versão 5.0 - APIs Oficiais Verificáveis")
    print(f"{'='*80}")
    print("\n✅ Este programa usa APENAS APIs oficiais")
    print("   Todos os dados são verificáveis via URL")
    print(f"{'='*80}")
    
    menu()