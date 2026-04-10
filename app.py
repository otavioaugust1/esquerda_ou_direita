"""
ANÁLISE POLÍTICA - Web App Flask
Aplicação web para análise de orientação política
baseada em publicações públicas de redes sociais.
"""

import os
import re as _re
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests as _req
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from analisador import executar_analise

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))


@app.route('/')
def index():
    """Página inicial com formulário de busca."""
    return render_template('index.html')


@app.route('/informacoes')
def informacoes():
    """Página de documentação completa."""
    return render_template('informacoes.html')


@app.route('/analisar', methods=['POST'])
def analisar():
    """Processa a análise política."""
    handle = request.form.get('handle', '').strip()
    nome = request.form.get('nome', '').strip()
    redes = request.form.getlist('redes')

    if not handle:
        return render_template('index.html', erro='Informe o @ do perfil.')

    # Limpar handle
    handle = handle.lstrip('@').strip()
    if not handle:
        return render_template('index.html', erro='Handle inválido.')

    if not redes:
        return render_template('index.html', erro='Selecione ao menos uma rede social.')

    resultado, erro = executar_analise(handle, nome if nome else None, redes_selecionadas=redes)

    if erro:
        return render_template('index.html', erro=erro)

    return render_template('resultado.html', r=resultado)


@app.route('/api/analisar', methods=['POST'])
def api_analisar():
    """Endpoint JSON para análise (uso programático)."""
    data = request.get_json(silent=True) or {}
    handle = data.get('handle', '').strip()
    nome = data.get('nome', '').strip()
    redes = data.get('redes', ['twitter', 'instagram', 'facebook'])

    if not handle:
        return jsonify({'erro': 'Handle obrigatório'}), 400

    resultado, erro = executar_analise(handle, nome if nome else None, redes_selecionadas=redes)

    if erro:
        return jsonify({'erro': erro}), 500

    return jsonify(resultado)


# ---------------------------------------------------------------------------
# API: Consulta à API aberta da Câmara dos Deputados
# ---------------------------------------------------------------------------

_CAMARA_API = 'https://dadosabertos.camara.leg.br/api/v2/deputados'
_CAMARA_HDR = {'User-Agent': 'esquerda_ou_direita/1.0', 'Accept': 'application/json'}
_RX_TW = _re.compile(r'(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})', _re.I)
_RX_IG = _re.compile(r'instagram\.com/([A-Za-z0-9_.]{1,50})', _re.I)


def _extrair_handles(redes):
    """Extrai handles do Twitter e Instagram a partir de lista de URLs."""
    if isinstance(redes, str):
        redes = [redes]
    tw = ig = None
    for url in (redes or []):
        if not url:
            continue
        if not tw:
            m = _RX_TW.search(url)
            if m:
                tw = m.group(1).lstrip('@').lower()
        if not ig:
            m = _RX_IG.search(url)
            if m:
                ig = m.group(1).rstrip('/').lower()
    return tw, ig


def _detalhar_deputado(dep):
    """Busca redes sociais do deputado pelo endpoint de detalhe."""
    dep_id = dep.get('id')
    tw = ig = None
    try:
        r = _req.get(f'{_CAMARA_API}/{dep_id}', headers=_CAMARA_HDR, timeout=8)
        if r.ok:
            dados = r.json().get('dados', {})
            ult = dados.get('ultimoStatus', {})
            redes = ult.get('urlRedeSocial') or dados.get('urlRedeSocial') or []
            tw, ig = _extrair_handles(redes)
    except Exception:
        pass
    return {
        'id': dep_id,
        'nome': dep.get('nome', ''),
        'partido': dep.get('siglaPartido', ''),
        'uf': dep.get('siglaUf', ''),
        'foto': dep.get('urlFoto', ''),
        'twitter': tw,
        'instagram': ig,
    }


@app.route('/api/buscar_deputado')
def api_buscar_deputado():
    """Busca deputados federais pelo nome ou ID na API da Câmara."""
    nome = request.args.get('nome', '').strip()
    dep_id = request.args.get('id', '').strip()

    if not nome and not dep_id:
        return jsonify({'erro': 'Informe nome ou ID do deputado'}), 400

    try:
        if dep_id:
            r = _req.get(f'{_CAMARA_API}/{dep_id}', headers=_CAMARA_HDR, timeout=10)
            if not r.ok:
                return jsonify({'erro': f'Deputado {dep_id} não encontrado'}), 404
            dados = r.json().get('dados', {})
            ult = dados.get('ultimoStatus', {})
            redes = ult.get('urlRedeSocial') or dados.get('urlRedeSocial') or []
            tw, ig = _extrair_handles(redes)
            resultado = [{
                'id': dados.get('id'),
                'nome': dados.get('nomeCivil') or dados.get('nome', ''),
                'partido': ult.get('siglaPartido', ''),
                'uf': ult.get('siglaUf', ''),
                'foto': ult.get('urlFoto', ''),
                'twitter': tw,
                'instagram': ig,
            }]
        else:
            r = _req.get(
                _CAMARA_API,
                params={'nome': nome, 'itens': 8, 'ordenarPor': 'nome', 'ordem': 'ASC'},
                headers=_CAMARA_HDR,
                timeout=10,
            )
            r.raise_for_status()
            lista = r.json().get('dados', [])[:6]
            resultado = []
            with ThreadPoolExecutor(max_workers=4) as ex:
                futs = {ex.submit(_detalhar_deputado, d): d for d in lista}
                for fut in as_completed(futs):
                    resultado.append(fut.result())
            resultado.sort(key=lambda x: x['nome'])

        return jsonify({'deputados': resultado})

    except Exception as e:
        return jsonify({'erro': str(e)[:120]}), 500

'''
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
    '''
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)