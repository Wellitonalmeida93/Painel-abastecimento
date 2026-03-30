import requests
import json
import os
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES DA TICKET LOG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
ARQUIVO_JSON = "transacoes.json"

# 🔥 LISTA DE CLIENTES (Frota e Agregado)
CODIGOS_CLIENTES = [122840, 206518] 

def carregar_historico():
    """Lê o arquivo gigante que já está no GitHub"""
    if os.path.exists(ARQUIVO_JSON):
        try:
            with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def buscar_dados_recentes():
    """Busca apenas os últimos 5 dias para atualizar o painel"""
    print("🔄 Iniciando atualização incremental (Últimos 5 dias)...")
    
    hoje = datetime.now()
    data_inicio = hoje - timedelta(days=5)
    
    transacoes_novas = []
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    
    # Percorre os últimos 5 dias
    data_atual = data_inicio
    while data_atual <= hoje:
        inicio_str = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim_str = data_atual.strftime("%Y-%m-%dT23:59:59")
        
        for cliente in CODIGOS_CLIENTES:
            origem = "FROTA" if cliente == 122840 else "AGREGADO"
            
            for considerar in ["V", "T"]:
                payload = {
                    "codigoCliente": cliente, "codigoTipoCartao": 4,
                    "dataTransacaoInicial": inicio_str,
                    "dataTransacaoFinal": fim_str,
                    "considerarTransacao": considerar, "ordem": "S", "validacao": "S"
                }
                
                try:
                    resp = requests.post(URL, json=payload, headers=headers, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("sucesso"):
                            notas = data.get("transacoes", [])
                            for n in notas:
                                n["origemConta"] = origem # Etiqueta para o painel
                            transacoes_novas.extend(notas)
                    elif resp.status_code == 500 and cliente == 206518:
                        # Blindagem: se o Agregado der erro de credencial, ignora e segue
                        print(f"⚠️ Cliente {cliente} (Agregado) sem acesso. Pulando...")
                        break 
                except:
                    continue
                time.sleep(0.5) # Pausa curta de segurança
                
        data_atual += timedelta(days=1)
        
    return transacoes_novas

if __name__ == "__main__":
    # 1. Carrega o passado (Ano todo que você subiu)
    dados_antigos = carregar_historico()
    print(f"📚 Histórico carregado: {len(dados_antigos)} notas.")
    
    # 2. Busca o futuro (Últimos 5 dias)
    dados_novos = buscar_dados_recentes()
    print(f"🆕 Notas recentes encontradas: {len(dados_novos)}")
    
    # 3. Une e Desduplica (Placa + Data + Valor)
    # Isso garante que notas que já estavam no arquivo não fiquem duplicadas
    tudo = dados_antigos + dados_novos
    
    print("🧹 Removendo duplicatas e ordenando...")
    unicos = {}
    for t in tudo:
        chave = f"{t.get('placa')}_{t.get('dataTransacao')}_{t.get('valorTransacao')}"
        unicos[chave] = t
        
    lista_final = list(unicos.values())
    lista_final.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
    
    # 4. Salva no GitHub
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Painel atualizado com sucesso! Total: {len(lista_final)} notas.")
