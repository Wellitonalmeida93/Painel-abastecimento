from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests
import time
import threading

app = Flask(__name__)

URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

TIPOS_CONSIDERACAO = ["V", "T"]

# 🔹 CACHE GLOBAL
cache_dados = []
ultima_atualizacao = None


# 🔹 CONSULTA API
def consultar_transacoes(data_inicio, data_fim, considerar):
    payload = {
        "codigoCliente": CODIGO_CLIENTE,
        "codigoTipoCartao": 4,
        "dataTransacaoInicial": data_inicio,
        "dataTransacaoFinal": data_fim,
        "considerarTransacao": considerar,
        "ordem": "S",
        "validacao": "S"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }

    try:
        response = requests.post(URL, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                return data.get("transacoes", [])
    except:
        pass

    return []


# 🔹 REMOVE DUPLICADOS
def remover_duplicados(transacoes):
    unicos = {}
    for t in transacoes:
        chave = t.get("codigoTransacao")
        if chave not in unicos:
            unicos[chave] = t
    return list(unicos.values())


# 🔹 CONSULTA COMPLETA
def atualizar_dados():
    global cache_dados, ultima_atualizacao

    print("🔄 Atualizando dados em background...")

    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)

    data_atual = inicio_mes
    todas = []

    while data_atual <= hoje:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")

        for tipo in TIPOS_CONSIDERACAO:
            resultado = consultar_transacoes(inicio, fim, tipo)
            todas.extend(resultado)

        data_atual += timedelta(days=1)
        time.sleep(1)

    cache_dados = remover_duplicados(todas)
    ultima_atualizacao = datetime.now()

    print(f"✅ Atualizado: {len(cache_dados)} registros")


# 🔹 THREAD BACKGROUND
def loop_atualizacao():
    while True:
        atualizar_dados()
        time.sleep(300)  # atualiza a cada 5 min


threading.Thread(target=loop_atualizacao, daemon=True).start()


# 🔹 ROTAS
@app.route("/")
def home():
    return "API rodando"

@app.route("/api/transacoes")
def api_transacoes():
    return jsonify({
        "total": len(cache_dados),
        "ultima_atualizacao": str(ultima_atualizacao),
        "dados": cache_dados
    })


if __name__ == "__main__":
    app.run()
