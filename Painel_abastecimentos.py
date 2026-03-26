from flask import Flask, jsonify, send_from_directory
from datetime import datetime, timedelta
import requests
import os

app = Flask(__name__, static_folder=".")

URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840


def consultar():
    hoje = datetime.now()
    inicio = hoje - timedelta(days=7)

    payload = {
        "codigoCliente": CODIGO_CLIENTE,
        "codigoTipoCartao": 4,
        "dataTransacaoInicial": inicio.strftime("%Y-%m-%dT00:00:00"),
        "dataTransacaoFinal": hoje.strftime("%Y-%m-%dT23:59:59"),
        "considerarTransacao": "T",
        "ordem": "S",
        "validacao": "S"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }

    try:
        response = requests.post(URL, json=payload, headers=headers, timeout=40)

        print("STATUS:", response.status_code)

        if response.status_code == 200:
            data = response.json()
            transacoes = data.get("transacoes", [])
            print("TOTAL:", len(transacoes))
            return transacoes
        else:
            print("ERRO API:", response.text)

    except Exception as e:
        print("ERRO GERAL:", str(e))

    return []


# 🔹 TESTE
@app.route("/api/teste")
def teste():
    return jsonify({"status": "ok"})


# 🔥 ROTA QUE FALTAVA
@app.route("/api/transacoes")
def transacoes():
    dados = consultar()
    return jsonify(dados)


# 🔹 INDEX
@app.route("/")
def home():
    return send_from_directory(".", "index.html")


# 🔹 RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
