import requests
import json
import os
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
ARQUIVO_JSON = "transacoes.json"

# 🔥 LISTA DE CLIENTES (O robô vai tentar os dois, mas não vai travar se um der erro)
CODIGOS_CLIENTES = [122840, 206518] 

def buscar_dados_seguros():
    print("🚀 Iniciando Busca de Segurança (Frota + Tentativa de Agregado)...")
    hoje = datetime.now()
    data_atual = hoje.replace(month=1, day=1) # Carga do ano todo
    
    transacoes_acumuladas = []
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    
    while data_atual <= hoje:
        dia_str = data_atual.strftime('%d/%m/%Y')
        print(f"📅 Processando: {dia_str}...")
        
        for cliente in CODIGOS_CLIENTES:
            origem = "FROTA" if cliente == 122840 else "AGREGADO"
            
            for considerar in ["V", "T"]:
                payload = {
                    "codigoCliente": cliente, "codigoTipoCartao": 4,
                    "dataTransacaoInicial": data_atual.strftime("%Y-%m-%dT00:00:00"),
                    "dataTransacaoFinal": data_atual.strftime("%Y-%m-%dT23:59:59"),
                    "considerarTransacao": considerar, "ordem": "S", "validacao": "S"
                }
                try:
                    resp = requests.post(URL, json=payload, headers=headers, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("sucesso"):
                            notas = data.get("transacoes", [])
                            for n in notas:
                                n["origemConta"] = origem # Nossa etiqueta oficial
                            transacoes_acumuladas.extend(notas)
                    elif resp.status_code == 500:
                        # 💡 AQUI ESTÁ A BLINDAGEM: Se der erro de credencial, ele só avisa e pula
                        if cliente == 206518:
                            print(f"  ⚠️ Agregado ({cliente}) ainda sem acesso na Ticket Log. Pulando...")
                            break # Pula os tipos V e T desse cliente no dia
                except Exception:
                    pass
                time.sleep(1) # Respeita o servidor
        data_atual += timedelta(days=1)
    
    return transacoes_acumuladas

if __name__ == "__main__":
    # 1. Busca os dados novos (Focando no que funciona)
    novos_dados = buscar_dados_seguros()
    
    if not novos_dados:
        print("❌ Nenhum dado foi retornado. Verifique a conexão.")
    else:
        # 2. Desduplicação Implacável (Placa + Data + Valor)
        # Isso vai matar aquelas duplicadas "PROPRIO" vs "FROTA"
        print(f"🧹 Desduplicando {len(novos_dados)} registros...")
        unicos = {}
        for t in novos_dados:
            chave = f"{t.get('placa')}_{t.get('dataTransacao')}_{t.get('valorTransacao')}"
            unicos[chave] = t
        
        lista_final = list(unicos.values())
        lista_final.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
        
        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(lista_final, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Sucesso! {len(lista_final)} transações salvas em {ARQUIVO_JSON}")
