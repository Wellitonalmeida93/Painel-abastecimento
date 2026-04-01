import requests
import json
import os
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES DA TICKET LOG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
ARQUIVO_JSON = "transacoes.json"
CODIGOS_CLIENTES = [122840, 206518] 

def carregar_historico():
    """Lê o arquivo existente no GitHub para não perder Janeiro a Março"""
    if os.path.exists(ARQUIVO_JSON):
        try:
            with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, list):
                    return dados
        except Exception as e:
            print(f"⚠️ Erro ao ler histórico: {e}")
    return []

def buscar_dados_recentes():
    """Busca os últimos 10 dias para garantir que não escape nada"""
    print("🔄 Acessando portal Ticket Log...")
    hoje = datetime.now()
    data_inicio = hoje - timedelta(days=10)
    
    transacoes_novas = []
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    
    data_atual = data_inicio
    while data_atual <= hoje:
        d_str = data_atual.strftime("%Y-%m-%d")
        print(f"📅 Verificando dia: {d_str}...", end=" ", flush=True)
        
        notas_dia = 0
        for cliente in CODIGOS_CLIENTES:
            origem = "FROTA" if cliente == 122840 else "AGREGADO"
            for tipo in ["V", "T"]:
                payload = {
                    "codigoCliente": cliente, "codigoTipoCartao": 4,
                    "dataTransacaoInicial": f"{d_str}T00:00:00",
                    "dataTransacaoFinal": f"{d_str}T23:59:59",
                    "considerarTransacao": tipo, "ordem": "S", "validacao": "S"
                }
                try:
                    resp = requests.post(URL, json=payload, headers=headers, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("sucesso"):
                            notas = data.get("transacoes", [])
                            for n in notas:
                                n["origemConta"] = origem
                            transacoes_novas.extend(notas)
                            notas_dia += len(notas)
                except:
                    continue
        print(f"OK ({notas_dia} notas)")
        data_atual += timedelta(days=1)
        time.sleep(0.3)
    return transacoes_novas

if __name__ == "__main__":
    # 1. Carrega o que já existe (Jan-Mar)
    historico_base = carregar_historico()
    total_antes = len(historico_base)
    print(f"📚 Base de dados atual: {total_antes} registros.")

    # 2. Busca notas recentes (Abril)
    novas_notas = buscar_dados_recentes()
    
    # 3. Mesclagem sem duplicados
    dic_unificado = {}
    for t in historico_base:
        chave = t.get('codigoTransacao') or f"{t.get('placa')}_{t.get('dataTransacao')}"
        dic_unificado[chave] = t

    for t in novas_notas:
        chave = t.get('codigoTransacao') or f"{t.get('placa')}_{t.get('dataTransacao')}"
        dic_unificado[chave] = t

    lista_final = list(dic_unificado.values())
    lista_final.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
    total_depois = len(lista_final)

    # 4. SALVAMENTO SEGURO (A TRAVA)
    if total_depois >= total_antes and total_depois > 0:
        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(lista_final, f, ensure_ascii=False, indent=2)
        print(f"✅ SUCESSO: BI atualizado! ({total_antes} -> {total_depois} registros)")
    else:
        print(f"❌ ERRO CRÍTICO: O robô tentou salvar {total_depois} notas, mas tínhamos {total_antes}.")
        print("Ação abortada para proteger o histórico de Janeiro a Março!")
