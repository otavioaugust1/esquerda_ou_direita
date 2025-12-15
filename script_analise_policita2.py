"""
ANÁLISE POLÍTICA SIMPLIFICADA - SEM DEPENDÊNCIAS EXTERNAS COMPLEXAS
Funciona com Python 3.8+
"""

import re
import json
from datetime import datetime, timedelta
from collections import Counter
import urllib.request
import urllib.parse
import time

# =========================
# CONFIGURAÇÃO
# =========================
USUARIOS_ALVO = [
    "LulaOficial",
    "jairbolsonaro", 
    "GuilhermeBoulos",
    "CarlaZambelli17",
    "JanonesGov",
    "fiscalizajacurso",
    "otavioaugust"
]

# =========================
# DICIONÁRIOS POLÍTICOS
# =========================
PALAVRAS_ESQUERDA = {
    # Palavras-chave
    "democracia", "direitos", "justiça", "social", "igualdade", "equidade",
    "sus", "saúde", "pública", "educação", "público", "trabalhador", "trabalhadora",
    "greve", "sindicato", "luta", "feminismo", "antiracismo", "antirracismo",
    "ambiental", "amazônia", "indígena", "quilombola", "reforma", "agrária",
    "pt", "lula", "dilma", "gleisi", "haddad", "boulos", "psol",
    "mst", "mtst", "movimento", "popular", "resistência", "oposição",
    
    # Hashtags
    "#forabolsonaro", "#lula", "#pt", "#pt13", "#elenão", "#elejamais",
    "#resistência", "#sus", "#saúdepública", "#educaçãopública",
    "#mariellepresente", "#vidasnegrasimportam", "#lgbt", "#direitos",
    "#grevegeral", "#democracia", "#feminismo", "#meioambiente"
}

PALAVRAS_DIREITA = {
    # Palavras-chave
    "liberdade", "livre", "mercado", "empreendedor", "empreendedora", "privatização",
    "meritocracia", "imposto", "impostos", "redução", "carga", "tributária",
    "família", "tradicional", "deus", "cristão", "cristã", "bíblia", "igreja",
    "conservador", "conservadora", "valores", "moral", "ética",
    "segurança", "pública", "armas", "legítima", "defesa",
    "patriota", "pátria", "brasil", "nacional", "soberania",
    "bolsonaro", "mito", "zambelli", "nikolas", "mbl", "novo", "psl",
    "comunismo", "comunista", "esquerda", "globalismo", "globalista",
    
    # Hashtags
    "#bolsonaro", "#mito", "#brasilacimadetudo", "#deusacimadetudo",
    "#intervenção", "#intervençãomilitar", "#verdadeeleitoral",
    "#escolasempartido", "#ideologiadegêneronão", "#família",
    "#conservador", "#liberdade", "#livremercado", "#menosimpostos",
    "#armamentista", "#direitodedefesa", "#patriota"
}

# Perfis para análise de menções/RTs
PERFIS_REF_ESQUERDA = {
    "lulaoficial", "gleisi", "haddad_fernando", "ptbrasil", "ptnacional",
    "guilhermeboulos", "psol50", "erikahiltonpsol", "mst_oficial"
}

PERFIS_REF_DIREITA = {
    "jairbolsonaro", "flaviobolsonaro", "carlosbolsonaro", "eduardobolsonaro",
    "carlazambelli17", "nikolas_ferreira", "pl_22", "mblivre"
}

# =========================
# FUNÇÕES DE BUSCA SIMPLES
# =========================
def buscar_conteudo_publico(usuario, plataforma="twitter"):
    """
    Busca conteúdo público de forma simples (sem API complexa).
    Nota: Esta é uma versão educacional simplificada.
    """
    
    # Dados de exemplo para teste (na prática, você usaria APIs ou web scraping)
    # Vou criar dados de exemplo baseados no perfil
    
    conteudos = []
    
    # Exemplos baseados no tipo de usuário
    if "lula" in usuario.lower() or "pt" in usuario.lower():
        conteudos = [
            "Defendendo a democracia e os direitos do povo brasileiro. #Lula #PT",
            "O SUS é um patrimônio do povo brasileiro que deve ser preservado.",
            "Pela educação pública de qualidade para todos os brasileiros.",
            "Apoio aos movimentos sociais e à reforma agrária.",
            "Contra o fascismo e pela liberdade. #ForaBolsonaro"
        ]
    elif "bolsonaro" in usuario.lower():
        conteudos = [
            "Pela liberdade e pelos valores da família brasileira. #Bolsonaro",
            "Defendendo o direito à legítima defesa e posse de armas.",
            "Contra o comunismo e pelo Brasil acima de tudo. #BrasilAcimaDeTudo",
            "Redução de impostos para os empreendedores brasileiros.",
            "Pela escola sem partido e valores cristãos. #DeusAcimaDeTudo"
        ]
    elif "boulos" in usuario.lower():
        conteudos = [
            "Luta por moradia digna para todas as famílias. #MoradiaÉDireito",
            "Contra a reforma da previdência que prejudica os trabalhadores.",
            "Pela taxação de grandes fortunas e justiça social.",
            "Defesa dos direitos LGBTQIA+ e das minorias.",
            "Apoio aos movimentos populares e à reforma urbana."
        ]
    else:
        # Conteúdo genérico
        conteudos = [
            "Bom dia! Espero que todos tenham um ótimo dia de trabalho.",
            "Compartilhando uma notícia importante sobre a economia.",
            "Participando de um evento cultural nesta semana.",
            "Refletindo sobre os desafios do nosso tempo.",
            "Agradecendo o apoio de todos os seguidores."
        ]
    
    # Adicionar alguns retweets simulados
    retweets = []
    if "lula" in usuario.lower():
        retweets = ["RT @ptbrasil: Pela democracia!", "RT @mst_oficial: Reforma agrária já!"]
    elif "bolsonaro" in usuario.lower():
        retweets = ["RT @pl_22: Pela família!", "RT @mblivre: Liberdade!"]
    
    return conteudos + retweets

# =========================
# ANÁLISE DE TEXTO
# =========================
def limpar_texto(texto):
    """Limpa e prepara o texto para análise"""
    texto = texto.lower()
    texto = re.sub(r'http\S+', '', texto)  # Remove URLs
    texto = re.sub(r'@(\w+)', '', texto)   # Remove menções (vamos analisar separadamente)
    texto = re.sub(r'[^\w\s#]', ' ', texto)  # Mantém palavras e hashtags
    return texto

def analisar_conteudo(conteudos):
    """Analisa uma lista de conteúdos e retorna scores"""
    score_esq = 0
    score_dir = 0
    total_posts = len(conteudos)
    
    if total_posts == 0:
        return 0, 0, 0, 0, 0
    
    for conteudo in conteudos:
        texto_limpo = limpar_texto(conteudo)
        palavras = texto_limpo.split()
        
        # Verificar se é RT
        eh_rt = conteudo.lower().startswith('rt @')
        peso = 2.0 if eh_rt else 1.0  # RT tem peso maior
        
        # Analisar palavras
        for palavra in palavras:
            if palavra in PALAVRAS_ESQUERDA:
                score_esq += peso
            elif palavra in PALAVRAS_DIREITA:
                score_dir += peso
        
        # Analisar menções em RTs
        if eh_rt:
            mencões = re.findall(r'@(\w+)', conteudo.lower())
            for mencao in mencões:
                if mencao in PERFIS_REF_ESQUERDA:
                    score_esq += 3.0  # Peso alto para RT de perfil de referência
                elif mencao in PERFIS_REF_DIREITA:
                    score_dir += 3.0
    
    return score_esq, score_dir, total_posts

# =========================
# CLASSIFICAÇÃO
# =========================
def classificar_usuario(usuario):
    """Classifica um usuário baseado no conteúdo"""
    
    print(f"\n🔍 Analisando @{usuario}...")
    
    # Buscar conteúdo (simulado)
    conteudos = buscar_conteudo_publico(usuario)
    
    if not conteudos:
        return {
            "usuario": usuario,
            "classificacao": "Sem conteúdo disponível",
            "esquerda": 0,
            "direita": 0,
            "neutro": 100,
            "posts": 0
        }
    
    # Analisar
    score_esq, score_dir, total_posts = analisar_conteudo(conteudos)
    
    # Calcular porcentagens
    total_score = score_esq + score_dir
    
    if total_score == 0:
        return {
            "usuario": usuario,
            "classificacao": "Neutro (sem indicadores políticos)",
            "esquerda": 0,
            "direita": 0,
            "neutro": 100,
            "posts": total_posts,
            "score_esq": 0,
            "score_dir": 0
        }
    
    pct_esq = (score_esq / total_score) * 100
    pct_dir = (score_dir / total_score) * 100
    pct_neutro = max(0, 100 - pct_esq - pct_dir)
    
    # Classificar
    if max(pct_esq, pct_dir) < 60:
        if pct_esq > pct_dir:
            classificacao = f"Neutro com inclinação à Esquerda ({pct_esq:.1f}%)"
        elif pct_dir > pct_esq:
            classificacao = f"Neutro com inclinação à Direita ({pct_dir:.1f}%)"
        else:
            classificacao = "Neutro (equilibrado)"
    else:
        if pct_esq > pct_dir:
            classificacao = f"Esquerda ({pct_esq:.1f}%)"
        else:
            classificacao = f"Direita ({pct_dir:.1f}%)"
    
    return {
        "usuario": usuario,
        "classificacao": classificacao,
        "esquerda": round(pct_esq, 1),
        "direita": round(pct_dir, 1),
        "neutro": round(pct_neutro, 1),
        "posts": total_posts,
        "score_esq": round(score_esq, 1),
        "score_dir": round(score_dir, 1)
    }

# =========================
# INTERFACE PRINCIPAL
# =========================
def main():
    """Função principal"""
    
    print("=" * 70)
    print("LABORATÓRIO DE ANÁLISE POLÍTICA - VERSÃO SIMPLIFICADA")
    print("=" * 70)
    print("⚠️  AVISO: Esta versão usa dados de exemplo para demonstração.")
    print("   Para análise real, conecte com APIs ou use web scraping.")
    print("=" * 70)
    
    resultados = []
    
    # Analisar cada usuário
    for usuario in USUARIOS_ALVO:
        resultado = classificar_usuario(usuario)
        resultados.append(resultado)
        time.sleep(0.5)  # Pausa para simular processamento
    
    # Exibir resultados
    print(f"\n{'='*70}")
    print("📊 RESULTADOS DA ANÁLISE")
    print(f"{'='*70}")
    print(f"{'USUÁRIO':<20} {'ESQUERDA':<10} {'DIREITA':<10} {'CLASSIFICAÇÃO':<30}")
    print(f"{'-'*70}")
    
    for res in resultados:
        print(f"@{res['usuario']:<18} {res['esquerda']:<9.1f}% {res['direita']:<9.1f}% {res['classificacao']}")
    
    # Estatísticas
    print(f"\n{'='*70}")
    print("📈 ESTATÍSTICAS")
    print(f"{'='*70}")
    
    esquerda = [r for r in resultados if 'Esquerda' in r['classificacao']]
    direita = [r for r in resultados if 'Direita' in r['classificacao']]
    neutros = [r for r in resultados if 'Neutro' in r['classificacao']]
    
    print(f"Total analisado: {len(resultados)} usuários")
    print(f"Esquerda: {len(esquerda)}")
    print(f"Direita: {len(direita)}")
    print(f"Neutros/Inclinados: {len(neutros)}")
    
    # Salvar resultados em JSON
    with open(f"resultados_analise_{datetime.now().strftime('%Y%m%d')}.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Resultados salvos em: resultados_analise_{datetime.now().strftime('%Y%m%d')}.json")
    print(f"\n{'='*70}")
    print("🎯 COMO MELHORAR ESTA ANÁLISE:")
    print("1. Conectar com API do Twitter (tweepy)")
    print("2. Implementar web scraping para conteúdo real")
    print("3. Expandir dicionários com mais palavras-chave")
    print("4. Adicionar análise de sentimentos")
    print("=" * 70)

# =========================
# VERSÃO PARA TESTE RÁPIDO
# =========================
def teste_rapido():
    """Teste rápido com um usuário específico"""
    
    usuario_teste = input("Digite o @ do usuário para análise (ex: LulaOficial): ").strip()
    
    if usuario_teste:
        resultado = classificar_usuario(usuario_teste)
        
        print(f"\n{'='*50}")
        print(f"RESULTADO PARA @{resultado['usuario']}")
        print(f"{'='*50}")
        print(f"📊 Pontuação:")
        print(f"  • Esquerda: {resultado['esquerda']}%")
        print(f"  • Direita:  {resultado['direita']}%")
        print(f"  • Neutro:   {resultado['neutro']}%")
        print(f"\n🏷️  Classificação:")
        print(f"  • {resultado['classificacao']}")
        print(f"\n📈 Detalhes:")
        print(f"  • Posts analisados: {resultado['posts']}")
        print(f"  • Score bruto esquerda: {resultado.get('score_esq', 0)}")
        print(f"  • Score bruto direita: {resultado.get('score_dir', 0)}")
        print(f"{'='*50}")

# =========================
# EXECUÇÃO
# =========================
if __name__ == "__main__":
    print("Escolha uma opção:")
    print("1. Analisar lista completa de usuários")
    print("2. Teste rápido com um usuário específico")
    
    opcao = input("Digite 1 ou 2: ").strip()
    
    if opcao == "2":
        teste_rapido()
    else:
        main()