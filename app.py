import os
import requests
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__, static_folder='.')

# 🔹 CONFIGURAÇÕES EXATAS DO SEU SCRIPT ORIGINAL
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840
TIPOS_CONSIDERACAO = ["V", "T"]

cache_dados = []
ultima_atualizacao = None

# Função que busca apenas UM dia específico
def buscar_dia(data_atual):
    inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
    fim = data_atual.strftime("%Y-%m-%dT23:59:59")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }
    
    transacoes_dia = []
    
    for considerar in TIPOS_CONSIDERACAO:
        # 🔹 PAYLOAD 100% IGUAL AO SEU (SEM CÓDIGO DO PRODUTO)
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
            resp = requests.post(URL, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("sucesso"):
                    transacoes_dia.extend(data.get("transacoes", []))
        except Exception as e:
            print(f"Erro ao buscar dia {inicio}: {e}")
            
    return transacoes_dia

def buscar_na_ticketlog():
    global cache_dados, ultima_atualizacao
    hoje = datetime.now()
    
    # Se já buscou nos últimos 10 minutos, devolve da memória na hora
    if cache_dados and ultima_atualizacao and (hoje - ultima_atualizacao).total_seconds() < 600:
        return cache_dados

    print("🔄 Iniciando Busca ACELERADA (Dias em Paralelo)...")
    
    inicio_mes = hoje.replace(day=1)
    dias_para_buscar = []
    data_atual = inicio_mes
    
    # Cria a lista com todos os dias do mês até hoje
    while data_atual <= hoje:
        dias_para_buscar.append(data_atual)
        data_atual += timedelta(days=1)
        
    todas = []
    
    # 🚀 MÁGICA: Dispara 5 buscas simultâneas para não dar Timeout!
    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = executor.map(buscar_dia, dias_para_buscar)
        for res in resultados:
            todas.extend(res)

    # Remove duplicados (Sua lógica)
    unicos = {t.get("codigoTransacao"): t for t in todas if t.get("codigoTransacao")}
    
    cache_dados = list(unicos.values())
    ultima_atualizacao = hoje
    
    print(f"✅ SUCESSO! {len(cache_dados)} transações carregadas em tempo recorde.")
    return cache_dados

# --- ROTAS DO SITE ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/dados')
def api_dados():
    dados = buscar_na_ticketlog()
    return jsonify(dados)

@app.route('/<path:path>')
def base_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)
