"""
Funções de análise de texto, pontuação e classificação política.
"""

import re
from collections import Counter

from .dados import (
    FIGURAS_POLITICAS,
    NOMES_DIREITA,
    NOMES_ESQUERDA,
    PALAVRAS_DIREITA,
    PALAVRAS_ESQUERDA,
)
from .utils import normalizar_texto

# Separar palavras simples de frases multi-token para análise correta
_PALAVRAS_ESQ_SIMPLES = frozenset(p for p in PALAVRAS_ESQUERDA if ' ' not in p)
_FRASES_ESQ = [p for p in PALAVRAS_ESQUERDA if ' ' in p]
_PALAVRAS_DIR_SIMPLES = frozenset(p for p in PALAVRAS_DIREITA if ' ' not in p)
_FRASES_DIR = [p for p in PALAVRAS_DIREITA if ' ' in p]

# Pré-normalizar nomes para eliminar bugs de acento
_NOMES_ESQ_NORM = [normalizar_texto(n) for n in NOMES_ESQUERDA]
_NOMES_DIR_NORM = [normalizar_texto(n) for n in NOMES_DIREITA]

# Mapa rápido: username normalizado → (nome, score) para detecção em texto
_FIGURAS_USERNAMES = frozenset(FIGURAS_POLITICAS.keys())

# Regex para capturar @menções
_RX_MENCOES = re.compile(r'@([A-Za-z0-9_]{2,40})')


def analisar_por_palavras(posts):
    """Analisa posts por palavras-chave e nomes conhecidos.
    Retorna pontuações, listas de palavras e evidências rastreáveis.
    """
    total_esq = 0
    total_dir = 0
    palavras_esq = []
    palavras_dir = []
    evidencias = []  # rastreio: termo → trecho + fonte

    # Para não repetir a mesma evidência dezenas de vezes
    _evidencias_vistas = set()

    for post in posts:
        texto_orig = post.get('texto', '')
        fonte = post.get('fonte', 'Desconhecida')
        texto_norm = normalizar_texto(texto_orig)
        palavras = re.findall(r'\b\w+\b', texto_norm)

        # Handles de figuras já pontuados NESTE post (evita double-count)
        _fig_pontuados = set()

        # --- Palavras-chave simples ---
        for palavra in palavras:
            if palavra in _PALAVRAS_ESQ_SIMPLES:
                total_esq += 1
                palavras_esq.append(palavra)
                _chave = ('esq', palavra)
                if _chave not in _evidencias_vistas:
                    _evidencias_vistas.add(_chave)
                    evidencias.append({
                        'termo': palavra, 'tipo': 'palavra-chave',
                        'lado': 'esq', 'peso': 1,
                        'trecho': texto_orig[:180], 'fonte': fonte,
                    })
            elif palavra in _PALAVRAS_DIR_SIMPLES:
                total_dir += 1
                palavras_dir.append(palavra)
                _chave = ('dir', palavra)
                if _chave not in _evidencias_vistas:
                    _evidencias_vistas.add(_chave)
                    evidencias.append({
                        'termo': palavra, 'tipo': 'palavra-chave',
                        'lado': 'dir', 'peso': 1,
                        'trecho': texto_orig[:180], 'fonte': fonte,
                    })

            # Verificar se a palavra é um username de FIGURAS_POLITICAS
            if palavra in _FIGURAS_USERNAMES and palavra not in _fig_pontuados:
                fig_nome, fig_score = FIGURAS_POLITICAS[palavra]
                if fig_score != 0:
                    _fig_pontuados.add(palavra)
                    peso = abs(fig_score) * 3
                    lado = 'esq' if fig_score < 0 else 'dir'
                    if fig_score < 0:
                        total_esq += peso
                        palavras_esq.append(fig_nome)
                    else:
                        total_dir += peso
                        palavras_dir.append(fig_nome)
                    _chave = ('fig', palavra)
                    if _chave not in _evidencias_vistas:
                        _evidencias_vistas.add(_chave)
                        evidencias.append({
                            'termo': fig_nome, 'tipo': 'handle-em-texto',
                            'lado': lado, 'peso': peso,
                            'trecho': texto_orig[:180], 'fonte': fonte,
                        })

        # --- Frases-chave (multi-token) ---
        for frase in _FRASES_ESQ:
            if frase in texto_norm:
                total_esq += 2
                palavras_esq.append(frase)
                _chave = ('esq', frase)
                if _chave not in _evidencias_vistas:
                    _evidencias_vistas.add(_chave)
                    evidencias.append({
                        'termo': frase, 'tipo': 'frase-chave',
                        'lado': 'esq', 'peso': 2,
                        'trecho': texto_orig[:180], 'fonte': fonte,
                    })
        for frase in _FRASES_DIR:
            if frase in texto_norm:
                total_dir += 2
                palavras_dir.append(frase)
                _chave = ('dir', frase)
                if _chave not in _evidencias_vistas:
                    _evidencias_vistas.add(_chave)
                    evidencias.append({
                        'termo': frase, 'tipo': 'frase-chave',
                        'lado': 'dir', 'peso': 2,
                        'trecho': texto_orig[:180], 'fonte': fonte,
                    })

        # --- Nomes políticos (normalizados para evitar bugs de acento) ---
        for nome in _NOMES_ESQ_NORM:
            if nome in texto_norm:
                total_esq += 2
                palavras_esq.append(nome.strip())
                _chave = ('esq', nome)
                if _chave not in _evidencias_vistas:
                    _evidencias_vistas.add(_chave)
                    evidencias.append({
                        'termo': nome, 'tipo': 'nome-politico',
                        'lado': 'esq', 'peso': 2,
                        'trecho': texto_orig[:180], 'fonte': fonte,
                    })
        for nome in _NOMES_DIR_NORM:
            if nome in texto_norm:
                total_dir += 2
                palavras_dir.append(nome.strip())
                _chave = ('dir', nome)
                if _chave not in _evidencias_vistas:
                    _evidencias_vistas.add(_chave)
                    evidencias.append({
                        'termo': nome, 'tipo': 'nome-politico',
                        'lado': 'dir', 'peso': 2,
                        'trecho': texto_orig[:180], 'fonte': fonte,
                    })

        # --- @menções de figuras políticas (ex: @LulaOficial, @CarlaZambelli) ---
        mencoes = _RX_MENCOES.findall(texto_orig)
        for mencao in mencoes:
            mencao_lower = mencao.lower()
            if mencao_lower in FIGURAS_POLITICAS and mencao_lower not in _fig_pontuados:
                fig_nome, fig_score = FIGURAS_POLITICAS[mencao_lower]
                if fig_score != 0:
                    _fig_pontuados.add(mencao_lower)
                    peso = abs(fig_score) * 3
                    lado = 'esq' if fig_score < 0 else 'dir'
                    if fig_score < 0:
                        total_esq += peso
                        palavras_esq.append(fig_nome)
                    else:
                        total_dir += peso
                        palavras_dir.append(fig_nome)
                    _chave = ('fig', mencao_lower)
                    if _chave not in _evidencias_vistas:
                        _evidencias_vistas.add(_chave)
                        evidencias.append({
                            'termo': f'@{mencao}', 'tipo': 'menção-figura',
                            'lado': lado, 'peso': peso,
                            'trecho': texto_orig[:180], 'fonte': fonte,
                        })

    return total_esq, total_dir, palavras_esq, palavras_dir, evidencias


def analisar_seguidores(seguindo_politicos):
    """Analisa figuras políticas seguidas (peso MUITO forte — 5x)."""
    score_esq = 0
    score_dir = 0
    figuras_esq = []
    figuras_dir = []

    vistos = set()
    for fig in seguindo_politicos:
        chave = fig.get('username', fig['nome'])
        if chave in vistos:
            continue
        vistos.add(chave)

        score = fig['score']
        nome = fig['nome']
        if score < 0:
            score_esq += abs(score) * 5
            figuras_esq.append(nome)
        elif score > 0:
            score_dir += score * 5
            figuras_dir.append(nome)

    return score_esq, score_dir, figuras_esq, figuras_dir


def classificar(pct_esq, pct_dir, total_pontos):
    """Gera classificação, descrição, confiança e cor."""
    if total_pontos < 1:
        return (
            'INCONCLUSIVO',
            'Dados insuficientes para esta plataforma',
            'NENHUMA',
            '#888888',
        )

    if total_pontos < 3:
        confianca = 'MUITO BAIXA'
    elif total_pontos < 10:
        confianca = 'BAIXA'
    elif total_pontos < 25:
        confianca = 'MÉDIA'
    else:
        confianca = 'ALTA'

    diff = abs(pct_esq - pct_dir)

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


def montar_resultado_plataforma(posts, seguindo_politicos=None):
    """Analisa uma lista de posts e retorna resultado de uma plataforma.
    Otimizado: limita posts para reduzir consumo de memória.
    """
    if seguindo_politicos is None:
        seguindo_politicos = []

    # Otimização: limitar posts para não exceder uso de memória
    # Manter apenas os 150 primeiros posts
    MAX_POSTS = 150
    if len(posts) > MAX_POSTS:
        posts = posts[:MAX_POSTS]

    (
        pts_esq_texto,
        pts_dir_texto,
        palavras_esq,
        palavras_dir,
        evidencias,
    ) = analisar_por_palavras(posts)
    pts_esq_seg, pts_dir_seg, figuras_esq, figuras_dir = analisar_seguidores(
        seguindo_politicos
    )

    # Adicionar evidências de figuras políticas seguidas
    for fig in seguindo_politicos:
        nome = fig.get('nome', '')
        score = fig.get('score', 0)
        fonte_det = fig.get('fonte_deteccao', 'Dados da plataforma')
        if score != 0:
            evidencias.append({
                'termo': nome,
                'tipo': 'seguindo-politico',
                'lado': 'esq' if score < 0 else 'dir',
                'peso': abs(score) * 5,
                'trecho': fig.get('descricao', '') or f"Segue @{fig.get('username', nome)}",
                'fonte': fonte_det,
            })

    total_esq = pts_esq_texto + pts_esq_seg
    total_dir = pts_dir_texto + pts_dir_seg
    total = total_esq + total_dir

    if total == 0:
        return {
            'total_posts': len(posts),
            'classificacao': 'INCONCLUSIVO',
            'descricao': 'Dados insuficientes para esta plataforma',
            'esquerda_pct': 0,
            'direita_pct': 0,
            'confianca': 'NENHUMA',
            'cor': '#888888',
            'pontos_esq': 0,
            'pontos_dir': 0,
            'top_palavras_esq': [],
            'top_palavras_dir': [],
            'seguindo_politicos': seguindo_politicos,
            'figuras_esq': list(set(figuras_esq))[:10],
            'figuras_dir': list(set(figuras_dir))[:10],
            'evidencias': [],
            'exemplos': [
                {'texto': p['texto'][:200], 'fonte': p['fonte']}
                for p in posts[:8]
            ],
        }

    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    classe, descricao, confianca, cor = classificar(pct_esq, pct_dir, total)

    return {
        'total_posts': len(posts),
        'classificacao': classe,
        'descricao': descricao,
        'esquerda_pct': round(pct_esq, 1),
        'direita_pct': round(pct_dir, 1),
        'confianca': confianca,
        'cor': cor,
        'pontos_esq': total_esq,
        'pontos_dir': total_dir,
        'top_palavras_esq': Counter(palavras_esq).most_common(10),
        'top_palavras_dir': Counter(palavras_dir).most_common(10),
        'seguindo_politicos': seguindo_politicos,
        'figuras_esq': list(set(figuras_esq))[:10],
        'figuras_dir': list(set(figuras_dir))[:10],
        'evidencias': evidencias,
        'exemplos': [
            {'texto': p['texto'][:200], 'fonte': p['fonte']} for p in posts[:8]
        ],
    }
