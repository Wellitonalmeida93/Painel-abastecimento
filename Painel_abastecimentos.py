import requests
import pandas as pd
from datetime import datetime, timedelta
import json

# 🔹 CONFIG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

TIPOS_CONSIDERACAO = ["V", "T"]


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

    response = requests.post(URL, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("sucesso"):
            return data.get("transacoes", [])
        else:
            print("Erro API:", data.get("mensagem"))

    return []


# 🔹 REMOVE DUPLICADOS
def remover_duplicados(transacoes):
    unicos = {}
    for t in transacoes:
        chave = t.get("codigoTransacao")
        if chave not in unicos:
            unicos[chave] = t
    return list(unicos.values())


# 🔹 CONSULTA PERÍODO
def consultar_periodo(data_inicio_str, data_fim_str):
    data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
    data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d")

    data_atual = data_inicio
    todas = []

    while data_atual <= data_fim:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")

        print(f"Consultando {data_atual.date()}")

        for considerar in TIPOS_CONSIDERACAO:
            resultado = consultar_transacoes(inicio, fim, considerar)
            todas.extend(resultado)

        data_atual += timedelta(days=1)

    return remover_duplicados(todas)


# 🔹 TRANSFORMA PARA TABELA
def transformar_para_tabela(transacoes):
    linhas = []

    for t in transacoes:
        linhas.append({
            "Data/Hora": t.get("dataTransacao"),
            "Placa": t.get("placa"),
            "Posto": t.get("nomeReduzidoEstabelecimento"),
            "Cidade": t.get("nomeCidade"),
            "Estado": t.get("uf"),
            "Produto": t.get("tipoCombustivel"),
            "Litros": t.get("litros"),
            "Valor Total": t.get("valorTransacao"),
            "Valor Unitário": t.get("valorLitro"),
            "Cartão": t.get("numeroCartao"),
            "Tipo": t.get("considerarTransacao")
        })

    return pd.DataFrame(linhas)


# 🔹 PERÍODO
DATA_INICIO = "2026-03-17"
DATA_FIM = "2026-03-24"


# 🔹 EXECUÇÃO
if __name__ == "__main__":
    transacoes = consultar_periodo(DATA_INICIO, DATA_FIM)

    print(f"Total de transações: {len(transacoes)}")

    # 🔹 Excel
    df = transformar_para_tabela(transacoes)
    nome_excel = f"abastecimentos_{DATA_INICIO}_a_{DATA_FIM}.xlsx"
    df.to_excel(nome_excel, index=False)

    print(f"Excel gerado: {nome_excel}")

    # 🔹 JSON (USADO NO PAINEL)
    with open("transacoes.json", "w", encoding="utf-8") as f:
        json.dump(transacoes, f, ensure_ascii=False, indent=2)

    print("JSON gerado com sucesso!")