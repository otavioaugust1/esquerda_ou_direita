"""
scraper_camara.py
=================
Busca todos os deputados federais no site da Câmara (camara.leg.br)
e tenta coletar handles de Twitter/X e Instagram de cada um.

Saída:
  - deputados_redes.json  → dados brutos completos
  - deputies_patch.py     → trecho pronto para colar em dados.py

Uso:
    pip install requests beautifulsoup4 lxml
    python scraper_camara.py

Parâmetros ajustáveis:
    MAX_WORKERS   — threads paralelas (padrão: 8)
    SLEEP_BETWEEN — pausa entre requests em segundos (padrão: 0.3)
"""

import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
API_DEPUTADOS   = "https://dadosabertos.camara.leg.br/api/v2/deputados"
API_DETALHE     = "https://dadosabertos.camara.leg.br/api/v2/deputados/{id}"
PERFIL_HTML     = "https://www.camara.leg.br/deputados/{id}"
MAX_WORKERS     = 8
SLEEP_BETWEEN   = 0.3   # segundos entre chamadas por thread
OUTPUT_JSON     = "deputados_redes.json"
OUTPUT_PATCH    = "deputies_patch.py"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DeputadosScraper/1.0; "
        "+https://github.com/seu-projeto)"
    )
}

# Mapeamento partido → score ideológico (base)
PARTIDO_SCORE = {
    # Esquerda
    "PT": -2, "PSOL": -2, "PCdoB": -2, "UP": -2, "PSTU": -2,
    # Centro-Esquerda
    "PSB": -1, "PDT": -1, "Rede": -1, "Solidariedade": -1,
    # Centro
    "MDB": 0, "PSD": 0, "Avante": 0, "Agir": 0, "Pros": 0,
    "Patriota": 0, "Cidadania": 0, "PRB": 0,
    # Centro-Direita
    "PP": 1, "PSDB": 1, "União": 1, "Republicanos": 1,
    "Podemos": 1, "NOVO": 1, "Pode": 1,
    # Direita
    "PL": 2, "PLC": 2, "PSC": 2, "PTB": 2,
}


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def slugify(text: str) -> str:
    """Remove acentos e caracteres especiais → minúsculo sem espaço."""
    nfkd = unicodedata.normalize("NFKD", text)
    only_ascii = nfkd.encode("ASCII", "ignore").decode("ASCII")
    return re.sub(r"[^a-z0-9_]", "", only_ascii.lower().replace(" ", "_"))


def score_partido(sigla: str) -> int:
    """Retorna score ideológico pelo partido; 0 se desconhecido."""
    for key, val in PARTIDO_SCORE.items():
        if key.lower() in sigla.lower():
            return val
    return 0


def extract_handles_from_html(html: str) -> dict[str, str]:
    """
    Extrai handles de Twitter/X e Instagram do HTML do perfil
    da Câmara. Retorna dict: {'twitter': '@handle', 'instagram': '@handle'}.
    """
    soup = BeautifulSoup(html, "lxml")
    handles: dict[str, str] = {}

    # O site da Câmara lista redes sociais em <a> com href externos
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()

        if "twitter.com" in href or "x.com" in href:
            # extrai o handle do URL
            m = re.search(r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})", href, re.I)
            if m:
                handle = m.group(1).lstrip("@")
                if handle.lower() not in ("intent", "share", "home", "search"):
                    handles["twitter"] = handle.lower()

        elif "instagram.com" in href:
            m = re.search(r"instagram\.com/([A-Za-z0-9_.]{1,50})", href, re.I)
            if m:
                handle = m.group(1).rstrip("/").lower()
                if handle not in ("p", "explore", "reel"):
                    handles["instagram"] = handle

    return handles


# ──────────────────────────────────────────────
# STEP 1 — lista todos os deputados via API aberta
# ──────────────────────────────────────────────
def fetch_all_deputies() -> list[dict]:
    """Retorna lista com todos os deputados da legislatura atual."""
    print("⏳  Buscando lista de deputados na API aberta da Câmara...")
    params = {"itens": 600, "ordem": "ASC", "ordenarPor": "nome"}
    r = requests.get(API_DEPUTADOS, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()["dados"]
    print(f"✅  {len(data)} deputados encontrados.")
    return data


# ──────────────────────────────────────────────
# STEP 2 — detalhe de cada deputado (inclui redes sociais na API)
# ──────────────────────────────────────────────
def fetch_deputy_detail(dep: dict) -> dict:
    """
    Busca detalhe do deputado:
      1. Tenta a API JSON (campo ultimoStatus.urlRedeSocial às vezes existe)
      2. Faz scraping da página HTML de perfil como fallback
    """
    dep_id = dep["id"]
    time.sleep(SLEEP_BETWEEN)

    result = {
        "id": dep_id,
        "nome": dep.get("nome", ""),
        "partido": dep.get("siglaPartido", ""),
        "uf": dep.get("siglaUf", ""),
        "twitter": None,
        "instagram": None,
    }

    # ── Tentativa 1: API JSON ──
    try:
        r = requests.get(
            API_DETALHE.format(id=dep_id), headers=HEADERS, timeout=15
        )
        if r.ok:
            detalhe = r.json().get("dados", {})
            ult = detalhe.get("ultimoStatus", {})
            # O campo urlRedeSocial pode ser uma lista ou string
            redes = ult.get("urlRedeSocial") or detalhe.get("urlRedeSocial") or []
            if isinstance(redes, str):
                redes = [redes]
            for url in redes:
                if not url:
                    continue
                url_lower = url.lower()
                if "twitter.com" in url_lower or "x.com" in url_lower:
                    m = re.search(
                        r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})", url, re.I
                    )
                    if m:
                        result["twitter"] = m.group(1).lower()
                elif "instagram.com" in url_lower:
                    m = re.search(
                        r"instagram\.com/([A-Za-z0-9_.]{1,50})", url, re.I
                    )
                    if m:
                        result["instagram"] = m.group(1).rstrip("/").lower()
    except Exception:
        pass

    # ── Tentativa 2: scraping HTML (se ainda sem handles) ──
    if not result["twitter"] and not result["instagram"]:
        try:
            r2 = requests.get(
                PERFIL_HTML.format(id=dep_id), headers=HEADERS, timeout=15
            )
            if r2.ok:
                handles = extract_handles_from_html(r2.text)
                result["twitter"]   = handles.get("twitter")
                result["instagram"] = handles.get("instagram")
        except Exception:
            pass

    return result


# ──────────────────────────────────────────────
# STEP 3 — gera trecho Python para dados.py
# ──────────────────────────────────────────────
def gerar_patch(deputados: list[dict]) -> str:
    """
    Gera o trecho de código Python para colar em FIGURAS_POLITICAS.
    Ignora deputados sem nenhum handle encontrado.
    """
    lines = []
    lines.append("# ════════════════════════════════════════")
    lines.append("# DEPUTADOS FEDERAIS — gerado por scraper_camara.py")
    lines.append("# ════════════════════════════════════════\n")

    grupos: dict[int, list[str]] = {-2: [], -1: [], 0: [], 1: [], 2: []}

    for dep in deputados:
        if not dep["twitter"] and not dep["instagram"]:
            continue  # sem rede social → pula

        score = score_partido(dep["partido"])
        nome  = dep["nome"]
        sigla = dep["partido"]
        uf    = dep["uf"]
        label = f"{nome} (Dep. {sigla}/{uf})"

        for plat, handle in [("twitter", dep["twitter"]), ("instagram", dep["instagram"])]:
            if handle:
                linha = f"    '{handle}': ('{label}', {score}),"
                grupos[score].append(linha)

    rotulos = {
        -2: "ESQUERDA (-2)",
        -1: "CENTRO-ESQUERDA (-1)",
         0: "CENTRO (0)",
         1: "CENTRO-DIREITA (1)",
         2: "DIREITA (2)",
    }
    for sc in [-2, -1, 0, 1, 2]:
        if grupos[sc]:
            lines.append(f"    # ── DEPUTADOS {rotulos[sc]} ──")
            lines.extend(grupos[sc])
            lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    # 1. Lista todos os deputados
    deputies_list = fetch_all_deputies()

    # 2. Busca detalhes em paralelo
    print(f"⏳  Buscando redes sociais de {len(deputies_list)} deputados "
          f"({MAX_WORKERS} threads)...")
    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_deputy_detail, dep): dep for dep in deputies_list}
        done = 0
        for future in as_completed(futures):
            done += 1
            res = future.result()
            results.append(res)
            tw  = res["twitter"]   or "—"
            ig  = res["instagram"] or "—"
            if done % 50 == 0 or done == len(deputies_list):
                print(f"   {done}/{len(deputies_list)} | "
                      f"{res['nome'][:30]:<30} tw={tw:<25} ig={ig}")

    # 3. Salva JSON bruto
    results.sort(key=lambda x: x["nome"])
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅  JSON salvo em: {OUTPUT_JSON}")

    # 4. Gera patch Python
    patch = gerar_patch(results)
    with open(OUTPUT_PATCH, "w", encoding="utf-8") as f:
        f.write('"""\n')
        f.write("Trecho gerado automaticamente por scraper_camara.py\n")
        f.write("Cole dentro de FIGURAS_POLITICAS em dados.py\n")
        f.write('"""\n\n')
        f.write(patch)
    print(f"✅  Patch Python salvo em: {OUTPUT_PATCH}")

    # 5. Resumo
    com_tw = sum(1 for d in results if d["twitter"])
    com_ig = sum(1 for d in results if d["instagram"])
    sem    = sum(1 for d in results if not d["twitter"] and not d["instagram"])
    print(f"\n📊  Resumo:")
    print(f"    Twitter/X encontrado : {com_tw}")
    print(f"    Instagram encontrado : {com_ig}")
    print(f"    Sem redes sociais    : {sem}")
    print(f"    Total                : {len(results)}")


if __name__ == "__main__":
    main()