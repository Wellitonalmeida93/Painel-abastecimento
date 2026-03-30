import requests
import json
import os
from datetime import datetime, timedelta
import time

URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
ARQUIVO_JSON = "transacoes.json"

CODIGOS_CLIENTES = [122840, 206518]

def carregar_dados_atuais():
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_dados(dados):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def carga_total_paciente():
    print("🚀 Iniciando Carga Total (Método Dia a Dia - Seguro)")
    
    hoje = datetime.now()
    data_atual = hoje.replace(month=1, day=1) # Começa em 01/01
    
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    
    while data_atual <= hoje:
        dia_str = data_atual.strftime('%d/%m/%Y')
        print(f"📅 Processando: {dia_str}...")
        
        # Carrega o que já temos para não perder nada se o programa parar
        base_atual = carregar_dados_atuais()
        novas_do_dia = []
        
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")
        
        for cliente in CODIGOS_CLIENTES:
            origem = "FROTA" if cliente == 122840 else "AGREGADO"
            
            for considerar in ["V", "T"]:
                payload = {
                    "codigoCliente": cliente, "codigoTipoCartao": 4,
                    "dataTransacaoInicial": inicio, "dataTransacaoFinal": fim,
                    "considerarTransacao": considerar, "ordem": "S", "validacao": "S"
                }
                try:
                    resp = requests.post(URL, json=payload, headers=headers, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("sucesso"):
                            lista = data.get("transacoes", [])
                            for nota in lista:
                                nota["origemConta"] = origem
                                novas_do_dia.append(nota)
                except Exception as e:
                    print(f"  ❌ Erro no dia {dia_str}: {e}")
                
                time.sleep(1.5) # Pausa de segurança entre requisições
        
        # Junta as novas do dia com a base, remove duplicatas e salva
        if novas_do_dia:
            print(f"  ✅ {len(novas_do_dia)} notas encontradas no dia {dia_str}.")
            tudo = base_atual + novas_do_dia
            
            # Desduplicação por Placa + Data + Valor
            limpos = {}
            for t in tudo:
                chave = f"{t.get('placa')}_{t.get('dataTransacao')}_{t.get('valorTransacao')}"
                limpos[chave] = t
            
            base_final = list(limpos.values())
            base_final.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
            salvar_dados(base_final)
        
        data_atual += timedelta(days=1)

if __name__ == "__main__":
    carga_total_paciente()
    print("\n✨ PROCESSO CONCLUÍDO COM SUCESSO!")
