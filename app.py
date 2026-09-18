import os
import json
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_folder='.')

ARQUIVO_JSON = "transacoes.json"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/dados')
def api_dados():
    # Lê o arquivo JSON gerado pelo robo.py
    if os.path.exists(ARQUIVO_JSON):
        try:
            with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception as e:
            print(f"Erro ao ler JSON: {e}")
            
    return jsonify([])

@app.route('/<path:path>')
def base_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Servidor BI rodando na porta {port}...")
    app.run(host='0.0.0.0', port=port)
