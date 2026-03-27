import os
import requests
from datetime import datetime
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_folder='.')

# --- CONFIGURAÇÕES TICKET LOG ---
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

# Memória temporária para o site não ficar lento
cache_dados = []
ultima_atualizacao = None

def buscar_na_ticketlog():
    global cache_dados, ultima_atualizacao
    
    agora = datetime.now()
    # Se já buscou nos últimos 10 minutos, usa a memória rápida!
    if cache_dados and ultima_atualizacao and (agora - ultima_atualizacao).total_seconds() < 600:
        return cache_dados

    print("🔄 Buscando dados fresquinhos na Ticket Log...")
    inicio_mes = agora.replace(day=1).strftime("%Y-%m-%dT00:00:00")
    fim_mes = agora.strftime("%Y-%m-%dT23:59:59")
    
    todas_transacoes = []
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    
    for tipo in ["V", "T"]:
        payload = {
            "codigoCliente": CODIGO_CLIENTE, "codigoTipoCartao": 4,
            "dataTransacaoInicial": inicio_mes, "dataTransacaoFinal": fim_mes,
            "considerarTransacao": tipo, "ordem": "S", "validacao": "S"
        }
        try:
            resp = requests.post(URL, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                dados = resp.json()
                if dados.get("sucesso"):
                    todas_transacoes.extend(dados.get("transacoes", []))
        except Exception as e:
            print(f"Erro na API: {e}")

    # Remove duplicados
    unicos = {t.get("codigoTransacao"): t for t in todas_transacoes if t.get("codigoTransacao")}
    
    # Atualiza a memória
    cache_dados = list(unicos.values())
    ultima_atualizacao = agora
    print(f"✅ Sucesso! {len(cache_dados)} abastecimentos encontrados.")
    
    return cache_dados

# --- ROTAS DO SITE ---

@app.route('/')
def index():
    # Entrega a tela visual (HTML)
    return send_from_directory('.', 'index.html')

@app.route('/api/dados')
def api_dados():
    # Esta é a rota invisível que o HTML vai chamar para pegar os dados
    dados = buscar_na_ticketlog()
    return jsonify(dados)

@app.route('/<path:path>')
def base_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
