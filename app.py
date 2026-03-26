from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests
import time

app = Flask(__name__)

URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

TIPOS_CONSIDERACAO = ["V", "T"]

# 🔹 CACHE
cache_dados = []
cache_tempo = None

# 🔹 CONSULTA API COM RETRY
def consultar_transacoes(data_inicio, data_fim, considerar, tentativas=3):
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

    for tentativa in range(tentativas):
        try:
            response = requests.post(URL, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get("sucesso"):
                    return data.get("transacoes", [])
                else:
                    return []
        except:
            pass

        time.sleep(2)

    return []


# 🔹 REMOVE DUPLICADOS
def remover_duplicados(transacoes):
    unicos = {}
    for t in transacoes:
        chave = t.get("codigoTransacao")
        if chave not in unicos:
            unicos[chave] = t
    return list(unicos.values())


# 🔹 CONSULTA PERÍODO (DIA A DIA)
def consultar_periodo():
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)

    data_atual = inicio_mes
    todas = []

    while data_atual <= hoje:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")

        for considerar in TIPOS_CONSIDERACAO:
            resultado = consultar_transacoes(inicio, fim, considerar)
            todas.extend(resultado)

        data_atual += timedelta(days=1)
        time.sleep(1)

    return remover_duplicados(todas)


# 🔹 ROTA TESTE
@app.route("/")
def home():
    return "API rodando"


# 🔹 ROTA PRINCIPAL (COM CACHE)
@app.route("/api/transacoes")
def api_transacoes():
    global cache_dados, cache_tempo

    agora = datetime.now()

    # Atualiza a cada 5 minutos
    if not cache_dados or not cache_tempo or (agora - cache_tempo).seconds > 300:
        print("🔄 Atualizando dados...")
        cache_dados = consultar_periodo()
        cache_tempo = agora
    else:
        print("⚡ Usando cache")

    return jsonify(cache_dados)


if __name__ == "__main__":
    app.run()
