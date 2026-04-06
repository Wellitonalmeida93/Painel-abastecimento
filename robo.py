import requests
import json
import os
import pandas as pd
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES
URL_TICKET = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
URL_PLANILHA_ACORDOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ-H-zThkjVd5_fooBo9vDrNNH_YNaxh9CNaGkULdD7hFtpmdSpQsEhlHhvbMX-IiEX5zZEjEIsZ-Pf/pub?gid=0&single=true&output=csv"
ARQUIVO_JSON = "transacoes.json"
CODIGOS_CLIENTES = [122840, 206518]

def carregar_acordos():
    try:
        df = pd.read_csv(URL_PLANILHA_ACORDOS)
        # Limpa o CNPJ (deixa só números)
        df['CNPJ_LIMPO'] = df['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
        return pd.Series(df['Diesel S10'].values, index=df['CNPJ_LIMPO']).to_dict()
    except Exception as e:
        print(f"⚠️ Erro ao ler planilha de acordos: {e}")
        return {}

def carregar_historico():
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def buscar_ticketlog_recente():
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    hoje = datetime.now()
    inicio = hoje - timedelta(days=10) # Busca só o recente para ser rápido
    novas = []
    
    data_alvo = inicio
    while data_alvo <= hoje:
        d_str = data_alvo.strftime("%Y-%m-%d")
        print(f"📅 Ticket Log (Busca Rápida): {d_str}...", end=" ", flush=True)
        n_dia = 0
        for cliente in CODIGOS_CLIENTES:
            origem = "FROTA" if cliente == 122840 else "AGREGADO"
            for tipo in ["V", "T"]:
                payload = {
                    "codigoCliente": cliente, "codigoTipoCartao": 4,
                    "dataTransacaoInicial": f"{d_str}T00:00:00", "dataTransacaoFinal": f"{d_str}T23:59:59",
                    "considerarTransacao": tipo, "ordem": "S", "validacao": "S"
                }
                try:
                    r = requests.post(URL_TICKET, json=payload, headers=headers, timeout=20)
                    if r.status_code == 200:
                        res = r.json()
                        if res.get("sucesso"):
                            for n in res.get("transacoes", []):
                                n["origemConta"] = origem
                                novas.append(n)
                                n_dia += 1
                except: continue
        print(f"OK ({n_dia})")
        data_alvo += timedelta(days=1)
        time.sleep(0.1)
    return novas

if __name__ == "__main__":
    acordos = carregar_acordos()
    historico = carregar_historico()
    total_base = len(historico)
    
    # 1. Pega as notas novas dos últimos 10 dias
    novas_notas = buscar_ticketlog_recente()
    
    # 2. Une histórico e novas num dicionário para evitar duplicidade
    unificado = { (t.get('codigoTransacao') or f"{t.get('placa')}_{t.get('dataTransacao')}"): t for t in historico }
    for n in novas_notas:
        chave = n.get('codigoTransacao') or f"{n.get('placa')}_{n.get('dataTransacao')}"
        unificado[chave] = n

    # 3. 🔥 AUDITORIA GERAL (Aplica em TODO o histórico de Jan a Abr)
    print(f"⚖️ Iniciando Auditoria Retroativa em {len(unificado)} registros...")
    for chave, n in unificado.items():
        # Limpa o CNPJ da nota
        cnpj = str(n.get("cnpjEstabelecimento", "")).replace(".","").replace("-","").replace("/","")
        preco_pago = n.get("valorLitro", 0)
        preco_teto = acordos.get(cnpj, 0)
        
        if preco_teto > 0:
            n["precoAcordado"] = preco_teto
            n["divergencia_un"] = round(preco_pago - preco_teto, 3)
            # Litros da nota
            vol = n.get("litros", 0)
            n["perda_total"] = round(n["divergencia_un"] * vol, 2)
            
            # Status para o BI
            if n["divergencia_un"] > 0.01:
                n["status_preco"] = "FORA"
            else:
                n["status_preco"] = "OK"
        else:
            n["status_preco"] = "N/C" # Posto não cadastrado na sua Planilha Google

    # 4. Ordena e salva
    lista_final = sorted(unificado.values(), key=lambda x: x.get("dataTransacao", ""), reverse=True)

    if len(lista_final) >= total_base:
        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(lista_final, f, ensure_ascii=False, indent=2)
        print(f"✅ SUCESSO! Histórico completo auditado ({len(lista_final)} notas).")
    else:
        print("❌ ERRO: Proteção contra perda de dados ativada.")
