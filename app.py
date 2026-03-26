from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests

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
    except Exception as e:
        print("Erro:", e)

    return []


@app.route("/")
def home():
    return "API rodando"


@app.route("/api/transacoes")
def transacoes():
    hoje = datetime.now()

    # 🔥 PEGA ÚLTIMOS 7 DIAS (GARANTE QUE VEM DADO)
    inicio = hoje - timedelta(days=7)

    data_inicio = inicio.strftime("%Y-%m-%dT00:00:00")
    data_fim = hoje.strftime("%Y-%m-%dT23:59:59")

    dados = consultar(data_inicio, data_fim)

    return jsonify({
        "dados": dados,
        "total": len(dados),
        "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M")
    })


if __name__ == "__main__":
    app.run()
