import requests
import json
import os
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES DA TICKET LOG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
ARQUIVO_JSON = "transacoes.json"

# 🔥 LISTA DE CLIENTES
CODIGOS_CLIENTES = [122840, 206518] 

def carregar_historico():
    """Lê o histórico existente para não perder o passado"""
    if os.path.exists(ARQUIVO_JSON):
        try:
            with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, list):
                    return dados
        except Exception as e:
            print(f"⚠️ Erro ao ler histórico: {e}. Iniciando do zero.")
    return []

def buscar_dados_recentes():
    """Busca os últimos 10 dias para garantir que não escape nada por atraso de processamento"""
    print("🔄 Buscando dados recentes na Ticket Log...")
    
    hoje = datetime.now()
    data_inicio = hoje - timedelta(days=10) # Aumentei para 10 dias por segurança
    
    transacoes_novas = []
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    
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
                    resp = requests.post(URL, json=payload, headers=headers, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("sucesso"):
                            notas = data.get("transacoes", [])
                            for n in notas:
                                n["origemConta"] = origem
                            transacoes_novas.extend(notas)
                    elif resp.status_code == 500 and cliente == 206518:
                        break 
                except:
                    continue
                time.sleep(0.3)
        
        data_atual += timedelta(days=1)
    return transacoes_novas

if __name__ == "__main__":
    # 1. Carrega o Histórico Acumulado
    historico_base = carregar_historico()
    print(f"📚 Registros no arquivo atual: {len(historico_base)}")
    
    # 2. Busca o que aconteceu recentemente
    novas_notas = buscar_dados_recentes()
    print(f"🆕 Notas baixadas do portal: {len(novas_notas)}")
    
    # 3. UNIÃO INTELIGENTE (Desduplicação por ID Único)
    # Usamos o código da transação da própria Ticket Log como chave
    dicionario_unificado = {}
    
    # Primeiro, colocamos o histórico no dicionário
    for t in historico_base:
        # Criamos uma ID única (codigoTransacao é o ideal, se não tiver usamos Placa+Data+Valor)
        id_unico = t.get('codigoTransacao') or f"{t.get('placa')}_{t.get('dataTransacao')}_{t.get('valorTransacao')}"
        dicionario_unificado[id_unico] = t

    # Depois, inserimos as novas (se a ID já existe, ele apenas atualiza/mantém)
    cont_novas_reais = 0
    for t in novas_notas:
        id_unico = t.get('codigoTransacao') or f"{t.get('placa')}_{t.get('dataTransacao')}_{t.get('valorTransacao')}"
        if id_unico not in dicionario_unificado:
            cont_novas_reais += 1
        dicionario_unificado[id_unico] = t
    
    # 4. Transforma de volta em lista e ordena por data
    lista_final = list(dicionario_unificado.values())
    lista_final.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
    
    # 5. Salva o arquivo GIGANTE atualizado
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Sucesso! {cont_novas_reais} novas notas adicionadas.")
    print(f"📊 Total acumulado no BI: {len(lista_final)} registros.")
