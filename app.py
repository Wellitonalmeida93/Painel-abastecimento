import os
import requests
from datetime import datetime
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_folder='.')

# --- CONFIGURAÇÕES TICKET LOG ---
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
TOKEN = "W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55" 
CODIGO_CLIENTE = 122840

# Memória temporária (cache) de 10 minutos para não travar o site
cache_dados = []
ultima_atualizacao = None

def buscar_na_ticketlog():
    global cache_dados, ultima_atualizacao
    
    agora = datetime.now()
    
    # Se já buscou nos últimos 10 minutos, devolve rápido da memória
    if cache_dados and ultima_atualizacao and (agora - ultima_atualizacao).total_seconds() < 600:
        return cache_dados

    print("🔄 Buscando dados na Ticket Log (Dia por Dia)...")
    
    todas_transacoes = []
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Basic {TOKEN}" 
    }
    
    ano_atual = agora.year
    mes_atual = agora.month
    dia_hoje = agora.day

    # Loop mágico: do dia 1 até o dia atual
    for dia in range(1, dia_hoje + 1):
        # Monta a data inicial e final para aquele dia específico
        data_inicial = f"{ano_atual}-{mes_atual:02d}-{dia:02d}T00:00:00"
        data_final = f"{ano_atual}-{mes_atual:02d}-{dia:02d}T23:59:59"
        
        print(f"Buscando dia {dia:02d}/{mes_atual:02d}...")
        
        for tipo in ["V", "T"]:
            payload = {
                "codigoCliente": CODIGO_CLIENTE, 
                "codigoTipoCartao": 4,
                "dataTransacaoInicial": data_inicial, 
                "dataTransacaoFinal": data_final,
                "considerarTransacao": tipo, 
                "ordem": "S", 
                "validacao": "S"
            }
            try:
                # Timeout curto para não prender o servidor se um dia falhar
                resp = requests.post(URL, json=payload, headers=headers, timeout=15)
                if resp.status_code == 200:
                    dados = resp.json()
                    if dados.get("sucesso"):
                        transacoes_do_dia = dados.get("transacoes", [])
                        todas_transacoes.extend(transacoes_do_dia)
            except Exception as e:
                print(f"❌ Erro de conexão no dia {dia}: {e}")

    # Remove transações duplicadas (caso a API mande repetido)
    unicos = {t.get("codigoTransacao"): t for t in todas_transacoes if t.get("codigoTransacao")}
    
    # Salva na memória
    cache_dados = list(unicos.values())
    ultima_atualizacao = agora
    
    print(f"✅ Concluído! {len(cache_dados)} abastecimentos encontrados no total.")
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
    # Threaded=True ajuda a não travar o servidor enquanto ele faz o loop dos dias
    app.run(host='0.0.0.0', port=port, threaded=True)
