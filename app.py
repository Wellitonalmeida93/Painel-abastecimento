import os
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify
import threading
import time

app = Flask(__name__, static_folder='.')

URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840
CACHE_FILE = "cache_transacoes.json"

def atualizar_dados_fundo():
    """Robô que roda no fundo devagar para não ser bloqueado e salva em arquivo"""
    while True:
        try:
            print("🔄 [Robô] Iniciando atualização em segundo plano...")
            hoje = datetime.now()
            inicio_mes = hoje.replace(day=1)
            data_atual = inicio_mes
            todas_transacoes = []
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": AUTHORIZATION
            }
            
            while data_atual <= hoje:
                inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
                fim = data_atual.strftime("%Y-%m-%dT23:59:59")
                
                for considerar in ["V", "T"]:
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
                                todas_transacoes.extend(data.get("transacoes", []))
                    except Exception as e:
                        pass # Ignora erros silenciosamente para não travar
                        
                data_atual += timedelta(days=1)
                time.sleep(1) # Pausa segura de 1 segundo (Idêntico ao seu script original)
            
            # Limpeza das duplicadas (Bate o valor de ~66 mil)
            unicos = {}
            for t in todas_transacoes:
                placa = t.get("placa", "SEM_PLACA")
                data_t = t.get("dataTransacao", "SEM_DATA")
                valor = t.get("valorTransacao", 0)
                chave = f"{placa}_{data_t}_{valor}"
                unicos[chave] = t
                
            dados_limpos = list(unicos.values())
            
            # Salva no arquivo (O Render consegue ler sem problema de memória)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(dados_limpos, f, ensure_ascii=False)
                
            print(f"✅ [Robô] Finalizado! {len(dados_limpos)} transações salvas.")
            
        except Exception as e:
            print(f"❌ Erro no robô: {e}")
            
        # Repete a cada 1 hora
        time.sleep(3600)

# Liga o robô assim que ligar o servidor
threading.Thread(target=atualizar_dados_fundo, daemon=True).start()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/dados')
def api_dados():
    # 1º Tenta pegar o arquivo fresquinho que o robô acabou de criar
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
            
    # 2º SALVA-VIDAS DA APRESENTAÇÃO: Puxa o seu JSON original que já funcionava!
    if os.path.exists('transacoes.json'):
        with open('transacoes.json', 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
            
    return jsonify([])

@app.route('/<path:path>')
def base_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
