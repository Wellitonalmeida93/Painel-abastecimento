import requests
import json
import os
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES DA TICKET LOG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
ARQUIVO_JSON = "transacoes.json"

# 🔥 LISTA DE CLIENTES: Frota e Agregados
CODIGOS_CLIENTES = [122840, 206518] 

def carregar_historico():
    if os.path.exists(ARQUIVO_JSON):
        try:
            with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            pass
    return []

def buscar_dados_ano_todo():
    print("🔄 Iniciando a busca na Ticket Log (MODO CARGA TOTAL E LIMPEZA)...")
    
    hoje = datetime.now()
    # Volta para 1º de Janeiro para limpar TUDO
    data_atual = hoje.replace(month=1, day=1)
    
    transacoes_novas = []
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    
    while data_atual <= hoje:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")
        
        print(f"   📅 Consultando dia {data_atual.strftime('%d/%m/%Y')}...")
        
        for cliente in CODIGOS_CLIENTES:
            # 🔥 NOME NOVO DA ETIQUETA PARA NÃO DAR CONFLITO COM A TICKET LOG 🔥
            if cliente == 122840:
                categoria = "FROTA"
            elif cliente == 206518:
                categoria = "AGREGADO"
            else:
                categoria = "OUTROS"
            
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
                            lista_notas = data.get("transacoes", [])
                            for nota in lista_notas:
                                # CARIMBA COM O NOME NOVO
                                nota["categoriaCliente"] = categoria 
                            transacoes_novas.extend(lista_notas)
                except Exception as e:
                    pass
                
                time.sleep(1) 
            
        data_atual += timedelta(days=1)
        
    return transacoes_novas

if __name__ == "__main__":
    dados_antigos = carregar_historico()
    dados_novos = buscar_dados_ano_todo()
    todas_transacoes = dados_antigos + dados_novos
    
    print("🧹 Aplicando Desduplicação Implacável (Modo Esmagador)...")
    unicos = {}
    for t in todas_transacoes:
        placa = t.get("placa", "SEM_PLACA")
        data_t = t.get("dataTransacao", "SEM_DATA")
        valor = t.get("valorTransacao", 0)
        
        # A chave blindada garante que a nota "PROPRIO" seja esmagada pela "FROTA"
        chave_blindada = f"{placa}_{data_t}_{valor}"
        unicos[chave_blindada] = t
        
    dados_limpos = list(unicos.values())
    dados_limpos.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
    
    print(f"✅ CARGA LIMPA CONCLUÍDA! Base com {len(dados_limpos)} transações perfeitas.")
    
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados_limpos, f, ensure_ascii=False, indent=2)
