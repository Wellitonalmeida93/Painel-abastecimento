import os
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify
import threading
import time

app = Flask(__name__, static_folder='.')

# 🔹 CONFIGURAÇÕES
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGOS_CLIENTES = [122840, 206518] # Frota e Agregados
CACHE_FILE = "cache_transacoes.json"
HISTORICO_FILE = "transacoes.json"
DATA_INICIO_RECENTE = datetime(2026, 4, 1) # A partir daqui o robô busca ao vivo

def atualizar_dados_fundo():
    """Robô que roda no fundo para buscar dados recentes, mesclar com o histórico e calcular KM"""
    while True:
        try:
            print("🔄 [Robô] Iniciando atualização em segundo plano...")
            hoje = datetime.now()
            data_atual = DATA_INICIO_RECENTE
            transacoes_recentes = []
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": AUTHORIZATION
            }
            
            # 1️⃣ BUSCA DADOS RECENTES (A PARTIR DE 01/04 ATÉ HOJE)
            while data_atual <= hoje:
                inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
                fim = data_atual.strftime("%Y-%m-%dT23:59:59")
                
                for cliente in CODIGOS_CLIENTES:
                    origem = "FROTA" if cliente == 122840 else "AGREGADO"
                    for considerar in ["V", "T"]:
                        payload = {
                            "codigoCliente": cliente,
                            "codigoTipoCartao": 4,
                            "dataTransacaoInicial": inicio,
                            "dataTransacaoFinal": fim,
                            "considerarTransacao": considerar,
                            "ordem": "S",
                            "validacao": "S"
                        }
                        
                        # Sistema de tentativas para evitar quedas da API
                        for tentativa in range(3):
                            try:
                                resp = requests.post(URL, json=payload, headers=headers, timeout=20)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    if data.get("sucesso"):
                                        notas = data.get("transacoes", [])
                                        for n in notas:
                                            n["origemConta"] = origem # Marca quem é frota/agregado
                                        transacoes_recentes.extend(notas)
                                    break # Deu certo, sai das tentativas
                            except Exception:
                                time.sleep(2)
                                
                data_atual += timedelta(days=1)
                time.sleep(0.5) # Pausa amigável

            # 2️⃣ CARREGA O HISTÓRICO (JANEIRO A MARÇO)
            historico = []
            if os.path.exists(HISTORICO_FILE):
                try:
                    with open(HISTORICO_FILE, 'r', encoding='utf-8') as f:
                        historico = json.load(f)
                except Exception as e:
                    print(f"⚠️ Erro ao ler histórico: {e}")

            # 3️⃣ MESCLA TUDO E REMOVE DUPLICADAS
            unicos = {}
            for t in historico + transacoes_recentes:
                chave = t.get("codigoTransacao") or f"{t.get('placa')}_{t.get('dataTransacao')}_{t.get('valorTransacao')}"
                unicos[chave] = t
                
            dados_unificados = list(unicos.values())
            
            # 4️⃣ CÁLCULO DO KM RODADO LINHA A LINHA
            # Ordena do mais antigo para o mais novo para o cálculo bater
            dados_unificados.sort(key=lambda x: (str(x.get("placa", "")), str(x.get("dataTransacao", ""))))
            
            km_anterior = {}
            for t in dados_unificados:
                placa = t.get("placa")
                try:
                    km_atual = float(t.get("quilometragem") or 0)
                except:
                    km_atual = 0
                    
                t["kmRodado"] = 0 # Valor padrão
                
                if placa and km_atual > 0:
                    if placa in km_anterior and km_anterior[placa] > 0:
                        diff = km_atual - km_anterior[placa]
                        if diff > 0:
                            t["kmRodado"] = diff
                    # Atualiza o km da placa para a próxima leitura
                    km_anterior[placa] = km_atual

            # 5️⃣ PREPARA PARA O SITE (Do mais novo pro mais antigo) E SALVA
            dados_unificados.sort(key=lambda x: str(x.get("dataTransacao", "")), reverse=True)
            
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(dados_unificados, f, ensure_ascii=False)
                
            print(f"✅ [Robô] Finalizado! {len(dados_unificados)} transações prontas para o painel.")
            
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
    # 1º Tenta pegar o arquivo fresquinho com o histórico + recentes + cálculos
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
            
    # 2º SALVA-VIDAS: Puxa o JSON histórico caso o robô ainda não tenha terminado a 1ª rodada
    if os.path.exists(HISTORICO_FILE):
        with open(HISTORICO_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
            
    return jsonify([])

@app.route('/<path:path>')
def base_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
