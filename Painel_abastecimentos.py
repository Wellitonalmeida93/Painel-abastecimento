import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time

# 🔹 CONFIG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

TIPOS_CONSIDERACAO = ["V", "T"]

# 🔹 CONSULTA API
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
                    print(f"Erro API: {data.get('mensagem')}")
                    return []
            else:
                print(f"Erro HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            print("Timeout, tentando novamente...")
        except requests.exceptions.RequestException as e:
            print(f"Erro conexão: {e}")

        time.sleep(5)

    return []

# 🔹 REMOVE DUPLICADOS
def remover_duplicados(transacoes):
    unicos = {}
    for t in transacoes:
        chave = t.get("codigoTransacao")
        if chave not in unicos:
            unicos[chave] = t
    return list(unicos.values())

# 🔹 CONSULTA PERÍODO (MÊS INTEIRO AUTOMÁTICO)
def consultar_mes_atual():
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)
    
    # último dia do mês
    if hoje.month == 12:
        proximo_mes = hoje.replace(year=hoje.year+1, month=1, day=1)
    else:
        proximo_mes = hoje.replace(month=hoje.month+1, day=1)
    
    fim_mes = proximo_mes - timedelta(days=1)

    data_atual = inicio_mes
    todas = []

    while data_atual <= fim_mes:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")

        print(f"Consultando {data_atual.date()}")

        for considerar in TIPOS_CONSIDERACAO:
            resultado = consultar_transacoes(inicio, fim, considerar)
            todas.extend(resultado)

        data_atual += timedelta(days=1)
        time.sleep(1)

    return remover_duplicados(todas)

# 🔹 TRANSFORMA PARA TABELA
def transformar_para_tabela(transacoes):
    linhas = []

    for t in transacoes:
        data_hora = t.get("dataTransacao")

        data = ""
        hora = ""

        if data_hora:
            dt = datetime.fromisoformat(data_hora)
            data = dt.strftime("%Y-%m-%d")
            hora = dt.strftime("%H:%M:%S")

        linhas.append({
            "Data": data,
            "Hora": hora,
            "Placa": t.get("placa"),
            "Posto": t.get("nomeReduzidoEstabelecimento"),
            "Cidade": t.get("nomeCidade"),
            "UF": t.get("uf"),
            "Produto": t.get("tipoCombustivel"),
            "Litros": t.get("litros"),
            "Valor Total": t.get("valorTransacao"),
            "Valor Unitário": t.get("valorLitro"),
            "Cartão": t.get("numeroCartao"),
            "Tipo": t.get("considerarTransacao")
        })

    return pd.DataFrame(linhas)

# 🔹 EXECUÇÃO
if __name__ == "__main__":
    print("🔄 Buscando dados do mês atual...")

    transacoes = consultar_mes_atual()

    print(f"Total de transações: {len(transacoes)}")

    # 🔹 Excel
    df = transformar_para_tabela(transacoes)
    nome_excel = "abastecimentos_mes_atual.xlsx"
    df.to_excel(nome_excel, index=False)

    print(f"Excel gerado: {nome_excel}")

    # 🔹 JSON (USADO NO SITE)
    with open("transacoes.json", "w", encoding="utf-8") as f:
        json.dump(transacoes, f, ensure_ascii=False, indent=2)

    print("JSON atualizado com sucesso!")
