import os
import requests
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify
import time

app = Flask(__name__, static_folder='.')

# 🔹 CONFIGURAÇÕES EXATAS DO SEU CÓDIGO ORIGINAL
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840
TIPOS_CONSIDERACAO = ["V", "T"]

# Memória temporária (cache) de 10 minutos
cache_dados = []
ultima_atualizacao = None

def buscar_na_ticketlog():
    global cache_dados, ultima_atualizacao
    
    hoje = datetime.now()
    
    # Se já buscou nos últimos 10 minutos, devolve rápido da memória
    if cache_dados and ultima_atualizacao and (hoje - ultima_atualizacao).total_seconds() < 600:
        return cache_dados

    print("🔄 Buscando dados do mês atual (Lógica Original PizzattoLog)...")
    
    inicio_mes = hoje.replace(day=1)
    data_atual = inicio_mes
    todas = []
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }

    # Loop igualzinho ao seu original, parando no dia de hoje
    while data_atual <= hoje:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")
        
        print(f"Consultando {data_atual.date()}...")
        
        for considerar in TIPOS_CONSIDERACAO:
            # PAYLOAD IDÊNTICO AO SEU SCRIPT
            payload = {
                "codigoCliente": CODIGO_CLIENTE,
                "codigoTipoCartao": 4,
                "dataTransacaoInicial": inicio,
                "dataTransacaoFinal": fim,
                "considerarTransacao": considerar,
                "ordem": "S",
                "validacao": "S"
            }
            
            try:
                response = requests.post(URL, json=payload, headers=headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("sucesso"):
                        todas.extend(data.get("transacoes", []))
            except Exception as e:
                print(f"❌ Erro na conexão: {e}")
                
        data_atual += timedelta(days=1)
        # Um pequeno sleep para não irritar a API da Ticket Log
        time.sleep(0.5)

    # REMOVE DUPLICADOS (Sua mesma função, mas otimizada)
    unicos = {t.get("codigoTransacao"): t for t in todas if t.get("codigoTransacao")}
    
    # Atualiza a memória
    cache_dados = list(unicos.values())
    ultima_atualizacao = hoje
    
    print(f"✅ SUCESSO ABSOLUTO! {len(cache_dados)} transações encontradas.")
    return cache_dados

# --- ROTAS DO SITE ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/dados')
def api_dados():
    # A tela HTML vai bater aqui, e o Python entrega os dados
    dados = buscar_na_ticketlog()
    return jsonify(dados)

@app.route('/<path:path>')
def base_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)
