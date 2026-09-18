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
        print(f"⚠️ Erro ao carregar acordos: {e}")
        return {}

def carregar_base_anp():
    """Lê o histórico da ANP gerado e cria um dicionário rápido de busca."""
    anp_dict = {}
    if os.path.exists("anp_historico_consolidado.csv"):
        try:
            df_anp = pd.read_csv("anp_historico_consolidado.csv", sep=";", encoding="utf-8-sig")
            df_anp['MUNICÍPIO'] = df_anp['MUNICÍPIO'].astype(str).str.strip().str.upper()
            df_anp['ESTADO'] = df_anp['ESTADO'].astype(str).str.strip().str.upper()
            
            for _, row in df_anp.iterrows():
                uf = row['ESTADO']
                cidade = row['MUNICÍPIO']
                produto = str(row['PRODUTO']).strip().upper()
                preco_medio = str(row['PREÇO MÉDIO REVENDA']).replace(',', '.')
                
                try:
                    preco_medio = float(preco_medio)
                except:
                    preco_medio = 0.0
                
                # Cria chave única: Ex: PR_CURITIBA_OLEO DIESEL S10
                chave = f"{uf}_{cidade}_{produto}"
                anp_dict[chave] = preco_medio
        except Exception as e:
            print(f"⚠️ Erro ao carregar base da ANP: {e}")
    else:
        print("⚠️ Arquivo anp_historico_consolidado.csv não encontrado no diretório.")
        
    return anp_dict

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
    print("🚀 Iniciando processamento do Cérebro (Ticket Log + Acordos + ANP)...")
    
    acordos = carregar_acordos_temporais()
    anp_dados = carregar_base_anp()
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
        # 1. Dados Básicos
        cnpj = str(n.get("cnpjEstablishment") or n.get("cnpjEstabelecimento") or "").replace(".","").replace("-","").replace("/","").zfill(14)
        preco_pago = n.get("valorLitro", 0)
        data_str = n.get("dataTransacao", "").split("T")[0]
        cidade_transacao = str(n.get("nomeCidade", "")).strip().upper()
        uf_transacao = str(n.get("uf", "")).strip().upper()
        produto_transacao = str(n.get("tipoCombustivel", "")).strip().upper()
        litros = n.get("litros", 0)
        
        try:
            data_transacao = pd.to_datetime(data_str)
        except:
            data_transacao = pd.to_datetime('today')

        # 2. Busca Preço Acordo
        preco_teto = 0
        lista_precos_posto = acordos.get(cnpj, [])
        for acordo in lista_precos_posto:
            if acordo['data'] <= data_transacao:
                preco_teto = acordo['preco']
        
        # 3. Busca Preço ANP
        if "S-10" in produto_transacao or "S10" in produto_transacao:
            prod_busca = "OLEO DIESEL S10"
        elif "DIESEL" in produto_transacao:
            prod_busca = "OLEO DIESEL"
        else:
            prod_busca = produto_transacao

        chave_anp = f"{uf_transacao}_{cidade_transacao}_{prod_busca}"
        preco_anp = anp_dados.get(chave_anp, 0.0)

        # 4. Injeta os 3 Pilares no JSON
        n["precoFrota"] = preco_pago
        n["precoAcordado"] = preco_teto
        n["precoANP"] = preco_anp
        
        # 5. Cálculos de Saving e Fugas
        if preco_teto > 0:
            n["divergencia_un"] = round(preco_pago - preco_teto, 3)
            n["perda_total"] = round(n["divergencia_un"] * litros, 2)
            n["status_preco"] = "FORA" if n["divergencia_un"] > 0.01 else ("ABAIXO" if n["divergencia_un"] < -0.01 else "OK")
        else:
            n["divergencia_un"] = 0
            n["perda_total"] = 0
            n["status_preco"] = "N/C"

        if preco_anp > 0:
            n["performance_anp_un"] = round(preco_pago - preco_anp, 3)
            n["saving_anp_total"] = round((preco_anp - preco_pago) * litros, 2)
        else:
            n["performance_anp_un"] = 0
            n["saving_anp_total"] = 0

    lista_salvar = sorted(lista_final, key=lambda x: x.get("dataTransacao", ""), reverse=True)

    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(lista_salvar, f, ensure_ascii=False, indent=2)
    print(f"\n✅ SUCESSO! Base consolidada com {len(lista_salvar)} transações, contendo Acordos e ANP.")
