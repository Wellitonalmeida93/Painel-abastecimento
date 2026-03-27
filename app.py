import os
import requests
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_folder='.')

# 🔹 CONFIGURAÇÕES EXATAS DO SEU SCRIPT
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

def buscar_teste_um_dia():
    print("\n" + "="*50)
    print("🔄 INICIANDO TESTE DE 1 DIA (Ontem)...")
    
    # Pegando a data de ontem para garantir que tem abastecimentos fechados
    ontem = datetime.now() - timedelta(days=1)
    data_str = ontem.strftime("%Y-%m-%d")
    
    inicio = f"{data_str}T00:00:00"
    fim = f"{data_str}T23:59:59"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }
    
    todas_transacoes = []
    
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
        
        print(f"\n👉 Enviando Payload ({considerar}): {payload}")
        
        try:
            resp = requests.post(URL, json=payload, headers=headers, timeout=20)
            print(f"👈 Resposta HTTP: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("sucesso"):
                    qtd = len(data.get("transacoes", []))
                    print(f"✅ SUCESSO! Encontrou {qtd} transações do tipo {considerar}.")
                    todas_transacoes.extend(data.get("transacoes", []))
                else:
                    print(f"⚠️ Erro da API Ticket Log: {data.get('mensagem')}")
            else:
                print(f"❌ Erro HTTP Completo: {resp.text}")
                
        except Exception as e:
            print(f"❌ Erro fatal de conexão: {e}")
            
    print("="*50 + "\n")
    return todas_transacoes

# --- ROTAS DO SITE ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/dados')
def api_dados():
    dados = buscar_teste_um_dia()
    return jsonify(dados)

@app.route('/<path:path>')
def base_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
