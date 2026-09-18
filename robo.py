import requests
import json
import os
import pandas as pd
import io
from datetime import datetime, timedelta, timezone
import time

URL_TICKET = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
URL_PLANILHA_ACORDOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ-H-zThkjVd5_fooBo9vDrNNH_YNaxh9CNaGkULdD7hFtpmdSpQsEhlHhvbMX-IiEX5zZEjEIsZ-Pf/pub?gid=0&single=true&output=csv"
ARQUIVO_JSON = "transacoes.json"

CODIGOS_CLIENTES = [122840, 206518]

def carregar_acordos_temporais():
    try:
        resposta = requests.get(URL_PLANILHA_ACORDOS, timeout=15)
        resposta.raise_for_status() 
        df = pd.read_csv(io.StringIO(resposta.text))
        
        if 'cnpj' in df.columns:
            df['CNPJ_LIMPO'] = df['cnpj'].astype(str).str.split('.').str[0].str.replace(r'\D', '', regex=True).str.zfill(14)
        else:
            return {}
        
        if 'Data' in df.columns:
            df['Data_Validade'] = pd.to_datetime(df['Data'], errors='coerce')
        else:
            df['Data_Validade'] = pd.NaT
            
        df['Data_Validade'] = df['Data_Validade'].fillna(pd.to_datetime('2000-01-01'))
        df = df.sort_values(by=['CNPJ_LIMPO', 'Data_Validade'])
        
        acordos_dict = {}
        for _, row in df.iterrows():
            cnpj = row['CNPJ_LIMPO']
            dt = row['Data_Validade']
            preco = row.get('Diesel S-10', 0)
            try:
                preco = float(str(preco).replace(',', '.'))
            except:
                preco = 0
            if cnpj not in acordos_dict:
                acordos_dict[cnpj] = []
            acordos_dict[cnpj].append({'data': dt, 'preco': preco})
        return acordos_dict
    except Exception as e:
        return {}

def carregar_historico():
    if os.path.exists(ARQUIVO_JSON):
        try:
            with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return []

def buscar_ticketlog_recente():
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    fuso_br = timezone(timedelta(hours=-3))
    hoje = datetime.now(fuso_br)
    
    # 🔥 AQUI ESTÁ A MÁGICA: Reduzido de 35 para 3 dias! Muito mais rápido.
    inicio = hoje - timedelta(days=3) 
    novas = []
    
    data_alvo = inicio
    while data_alvo <= hoje:
        d_str = data_alvo.strftime("%Y-%m-%d")
        print(f"📅 Buscando: {d_str}...", end=" ", flush=True)
        n_dia = 0
        
        for cliente in CODIGOS_CLIENTES:
            origem = "FROTA" if cliente == 122840 else "AGREGADO"
            
            for tipo_cartao in [1, 2, 3, 4]: 
                for tipo in ["V", "T"]:
                    for val_status in ["S", "N"]: 
                        payload = {
                            "codigoCliente": cliente, 
                            "codigoTipoCartao": tipo_cartao,
                            "dataTransacaoInicial": f"{d_str}T00:00:00", 
                            "dataTransacaoFinal": f"{d_str}T23:59:59",
                            "considerarTransacao": tipo, 
                            "ordem": "S", 
                            "validacao": val_status,
                            "numeroPagina": 1, 
                            "quantidadeRegistros": 5000  
                        }
                        try:
                            r = requests.post(URL_TICKET, json=payload, headers=headers, timeout=20)
                            if r.status_code == 200:
                                res = r.json()
                                if res.get("sucesso"):
                                    for n in res.get("transacoes", []):
                                        n["origemConta"] = origem
                                        n["considerarTransacao"] = tipo
                                        novas.append(n)
                                        n_dia += 1
                        except: 
                            continue 
        print(f"OK ({n_dia})")
        data_alvo += timedelta(days=1)
        time.sleep(0.1)
    return novas

if __name__ == "__main__":
    acordos = carregar_acordos_temporais()
    historico = carregar_historico()
    novas_notas = buscar_ticketlog_recente()
    
    unificado = {}
    for t in historico:
        chave = str(t.get('id') or t.get('codigoTransacao') or '') + "_" + str(t.get('placa') or '') + "_" + str(t.get('dataTransacao') or '')
        unificado[chave] = t

    for n in novas_notas:
        chave = str(n.get('id') or n.get('codigoTransacao') or '') + "_" + str(n.get('placa') or '') + "_" + str(n.get('dataTransacao') or '')
        unificado[chave] = n

    lista_final = list(unificado.values())
    
    for n in lista_final:
        cnpj = str(n.get("cnpjEstablishment") or n.get("cnpjEstabelecimento") or "").replace(".","").replace("-","").replace("/","").zfill(14)
        preco_pago = n.get("valorLitro", 0)
        data_str = n.get("dataTransacao", "").split("T")[0]
        
        try:
            data_transacao = pd.to_datetime(data_str)
        except:
            data_transacao = pd.to_datetime('today')

        preco_teto = 0
        lista_precos_posto = acordos.get(cnpj, [])
        for acordo in lista_precos_posto:
            if acordo['data'] <= data_transacao:
                preco_teto = acordo['preco']
        
        if preco_teto > 0:
            n["precoAcordado"] = preco_teto
            n["divergencia_un"] = round(preco_pago - preco_teto, 3)
            n["perda_total"] = round(n["divergencia_un"] * n.get("litros", 0), 2)
            n["status_preco"] = "FORA" if n["divergencia_un"] > 0.01 else ("ABAIXO" if n["divergencia_un"] < -0.01 else "OK")
        else:
            n["status_preco"] = "N/C"

    lista_salvar = sorted(lista_final, key=lambda x: x.get("dataTransacao", ""), reverse=True)

    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(lista_salvar, f, ensure_ascii=False, indent=2)
    print(f"✅ SUCESSO! Base atualizada com {len(lista_salvar)} notas.")
