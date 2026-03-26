from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests
import time

app = Flask(__name__)

URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

def consultar(data_inicio, data_fim):
    payload = {
        "codigoCliente": CODIGO_CLIENTE,
        "codigoTipoCartao": 4,
        "dataTransacaoInicial": data_inicio,
        "dataTransacaoFinal": data_fim,
        "considerarTransacao": "T",
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
            return data.get("transacoes", [])
    except:
        return []

    return []

@app.route("/api/transacoes")
def api_transacoes():

    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)

    data_inicio = inicio_mes.strftime("%Y-%m-%dT00:00:00")
    data_fim = hoje.strftime("%Y-%m-%dT23:59:59")

    dados = consultar(data_inicio, data_fim)

    return jsonify(dados)

if __name__ == "__main__":
    app.run()