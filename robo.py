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

def carregar_acordos_temporais():
    """Lê a planilha e organiza os preços por CNPJ e Data"""
    try:
        df = pd.read_csv(URL_PLANILHA_ACORDOS)
        df['CNPJ_LIMPO'] = df['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
        
        # Tenta ler a coluna de Data (se não existir ou estiver vazia, assume ano 2000 para valer sempre)
        if 'Data Acordo' in df.columns:
            df['Data_Validade'] = pd.to_datetime(df['Data Acordo'], format='%d/%m/%Y', errors='coerce')
        else:
            df['Data_Validade'] = pd.NaT
            
        df['Data_Validade'] = df['Data_Validade'].fillna(pd.to_datetime('2000-01-01'))
        
        # Ordena cronologicamente para garantir que pegamos o mais recente
        df = df.sort_values(by=['CNPJ_LIMPO', 'Data_Validade'])
        
        acordos_dict = {}
        for _, row in df.iterrows():
            cnpj = row['CNPJ_LIMPO']
            dt = row['Data_Validade']
            preco = row['Diesel S10']
            
            if cnpj not in acordos_dict:
                acordos_dict[cnpj] = []
            acordos_dict[cnpj].append({'data': dt, 'preco': preco})
            
        return acordos_dict
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
    inicio = hoje - timedelta(days=10)
    novas = []
    
    data_alvo = inicio
    while data_alvo <= hoje:
        d_str = data_alvo.strftime("%Y-%m-%d")
        print(f"📅 Ticket Log: {d_str}...", end=" ", flush=True)
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
    acordos = carregar_acordos_temporais()
    historico = carregar_historico()
    total_base = len(historico)
    
    novas_notas = buscar_ticketlog_recente()
    unificado = { (t.get('codigoTransacao') or f"{t.get('placa')}_{t.get('dataTransacao')}"): t for t in historico }
    
    for n in novas_notas:
        chave = n.get('codigoTransacao') or f"{n.get('placa')}_{n.get('dataTransacao')}"
        unificado[chave] = n

    print(f"⚖️ Iniciando Auditoria Temporal em {len(unificado)} registros...")
    
    for chave, n in unificado.items():
        cnpj = str(n.get("cnpjEstabelecimento", "")).replace(".","").replace("-","").replace("/","")
        preco_pago = n.get("valorLitro", 0)
        
        # Descobre a data da transação
        data_str = n.get("dataTransacao", "").split("T")[0]
        try:
            data_transacao = pd.to_datetime(data_str)
        except:
            data_transacao = pd.to_datetime('today')

        # Busca o preço teto correspondente à data
        preco_teto = 0
        lista_precos_posto = acordos.get(cnpj, [])
        
        # Como está ordenado, o último preço onde a data do acordo é <= data da transação é o vencedor
        for acordo in lista_precos_posto:
            if acordo['data'] <= data_transacao:
                preco_teto = acordo['preco']
        
        if preco_teto > 0:
            n["precoAcordado"] = preco_teto
            n["divergencia_un"] = round(preco_pago - preco_teto, 3)
            n["perda_total"] = round(n["divergencia_un"] * n.get("litros", 0), 2)
            n["status_preco"] = "FORA" if n["divergencia_un"] > 0.01 else "OK"
        else:
            n["status_preco"] = "N/C" 

    lista_final = sorted(unificado.values(), key=lambda x: x.get("dataTransacao", ""), reverse=True)

    if len(lista_final) >= total_base or total_base == 0:
        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(lista_final, f, ensure_ascii=False, indent=2)
        print(f"✅ SUCESSO! Base salva com {len(lista_final)} notas.")
    else:
        print("❌ ERRO: Proteção contra perda de dados. Abortado.")
