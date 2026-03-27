import os
import requests
from datetime import datetime
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_folder='.')

# --- CONFIGURAÇÕES TICKET LOG ---
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
TOKEN = "W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55" 
CODIGO_CLIENTE = 122840

cache_dados = []
ultima_atualizacao = None

def buscar_na_ticketlog():
    global cache_dados, ultima_atualizacao
    
    agora = datetime.now()
    if cache_dados and ultima_atualizacao and (agora - ultima_atualizacao).total_seconds() < 600:
        return cache_dados

    print("🔄 Iniciando busca limpa na Ticket Log (Dia por Dia)...")
    
    todas_transacoes = []
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Basic {TOKEN}" 
    }
    
    ano_atual = agora.year
    mes_atual = agora.month
    dia_hoje = agora.day

    for dia in range(1, dia_hoje + 1):
        data_inicial = f"{ano_atual}-{mes_atual:02d}-{dia:02d}T00:00:00"
        data_final = f"{ano_atual}-{mes_atual:02d}-{dia:02d}T23:59:59"
        
        for tipo in ["V", "T"]:
            # PAYLOAD LIMPO: Sem filtros fantasmas!
            payload = {
                "codigoCliente": CODIGO_CLIENTE, 
                "dataTransacaoInicial": data_inicial, 
                "dataTransacaoFinal": data_final,
                "considerarTransacao": tipo
            }
            
            try:
                resp = requests.post(URL, json=payload, headers=headers, timeout=15)
                
                # MEGA RAIO-X: Imprime exatamente o que a API devolveu
                print(f"Dia {dia:02d} (Tipo {tipo}) -> Status: {resp.status_code} | Resposta: {resp.text[:150]}...")
                
                if resp.status_code == 200:
                    dados = resp.json()
                    if dados.get("sucesso"):
                        transacoes_do_dia = dados.get("transacoes", [])
                        todas_transacoes.extend(transacoes_do_dia)
            except Exception as e:
                print(f"❌ Erro de conexão no dia {dia}: {e}")

    unicos = {t.get("codigoTransacao"): t for t in todas_transacoes if t.get("codigoTransacao")}
    cache_dados = list(unicos.values())
    ultima_atualizacao = agora
    
    print(f"✅ FIM DA BUSCA! {len(cache_dados)} abastecimentos encontrados.")
    return cache_dados

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
