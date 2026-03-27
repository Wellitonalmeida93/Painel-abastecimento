import os
import requests
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify
import threading
import time

app = Flask(__name__, static_folder='.')

# 🔹 CONFIGURAÇÕES DA TICKET LOG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

# Memória global do site
cache_dados = []
atualizando = False

def buscar_um_dia(data_alvo):
    """Busca os abastecimentos de apenas 1 dia específico"""
    data_str = data_alvo.strftime("%Y-%m-%d")
    inicio = f"{data_str}T00:00:00"
    fim = f"{data_str}T23:59:59"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }
    
    transacoes_dia = []
    
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
                    transacoes_dia.extend(data.get("transacoes", []))
        except Exception as e:
            print(f"Erro no dia {data_str}: {e}")
            
    return transacoes_dia

def atualizar_dados_no_fundo():
    """O Robô que roda escondido buscando o mês inteiro sem travar o site"""
    global cache_dados, atualizando
    
    if atualizando:
        return
    atualizando = True
    
    print("🤖 Iniciando o Robô: Limpando duplicadas e buscando dados...")
    
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)
    
    data_atual = hoje
    todas_transacoes = []
    
    # Busca de HOJE descendo até o DIA 1
    while data_atual >= inicio_mes:
        print(f"   ⏳ Baixando dados de {data_atual.strftime('%d/%m/%Y')}...")
        novas_transacoes = buscar_um_dia(data_atual)
        todas_transacoes.extend(novas_transacoes)
        
        # 🔹 A MÁGICA DA DESDUPLICAÇÃO IMPLACÁVEL 🔹
        # Cria uma chave única: Placa + Data/Hora Exata + Valor
        unicos = {}
        for t in todas_transacoes:
            placa = t.get("placa", "SEM_PLACA")
            data_t = t.get("dataTransacao", "SEM_DATA")
            valor = t.get("valorTransacao", 0)
            
            # Se a Ticket Log mandar 2, 3 ou 10 vezes a mesma coisa, só passa 1!
            chave_blindada = f"{placa}_{data_t}_{valor}"
            unicos[chave_blindada] = t
            
        cache_dados = list(unicos.values())
        
        # Desce um dia e pausa para não irritar a Ticket Log
        data_atual -= timedelta(days=1)
        time.sleep(1)
        
    print(f"✅ ROBÔ TERMINOU! Mês fechado com valores reais: {len(cache_dados)} transações limpas.")
    atualizando = False
    
    # Programa para rodar de novo daqui a 2 horas (7200 segundos) automaticamente
    threading.Timer(7200, atualizar_dados_no_fundo).start()

# LIGA O ROBÔ ASSIM QUE O SERVIDOR ACORDAR
threading.Thread(target=atualizar_dados_no_fundo, daemon=True).start()

# --- ROTAS DO SITE ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/dados')
def api_dados():
    # O site pede os dados, a gente devolve a memória na hora
    return jsonify(cache_dados)

@app.route('/<path:path>')
def base_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
