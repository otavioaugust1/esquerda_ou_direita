"""
ANÁLISE POLÍTICA - Web App Flask
Aplicação web para análise de orientação política
baseada em publicações públicas de redes sociais.
"""

import os
import secrets

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

    if not handle:
        return render_template('index.html', erro='Informe o @ do perfil.')

    # Limpar handle
    handle = handle.lstrip('@').strip()
    if not handle:
        return render_template('index.html', erro='Handle inválido.')

    resultado, erro = executar_analise(handle, nome if nome else None)

    if erro:
        return render_template('index.html', erro=erro)

    return render_template('resultado.html', r=resultado)


@app.route('/api/analisar', methods=['POST'])
def api_analisar():
    """Endpoint JSON para análise (uso programático)."""
    data = request.get_json(silent=True) or {}
    handle = data.get('handle', '').strip()
    nome = data.get('nome', '').strip()

    if not handle:
        return jsonify({'erro': 'Handle obrigatório'}), 400

    resultado, erro = executar_analise(handle, nome if nome else None)

    if erro:
        return jsonify({'erro': erro}), 500

    return jsonify(resultado)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
