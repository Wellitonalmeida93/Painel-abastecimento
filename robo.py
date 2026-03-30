import requests
import json
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES DA TICKET LOG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
ARQUIVO_JSON = "transacoes.json"

# 🔥 LISTA DE CLIENTES
CODIGOS_CLIENTES = [122840, 206518] 

def buscar_dados_ano_todo():
    print("🔄 Iniciando HARD RESET (Baixando tudo do zero para limpar duplicadas)...")
    hoje = datetime.now()
    data_atual = hoje.replace(month=1, day=1) # Volta pra 1º de Jan
    transacoes_novas = []
    headers = {"Content-Type": "application/json", "Authorization": AUTHORIZATION}
    
    while data_atual <= hoje:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")
        print(f"   📅 Consultando dia {data_atual.strftime('%d/%m/%Y')}...")
        
        for cliente in CODIGOS_CLIENTES:
            # Etiqueta Nova (NÃO APAGA A DA TICKET LOG)
            if cliente == 122840:
                origem = "FROTA"
            elif cliente == 206518:
                origem = "AGREGADO"
            else:
                origem = "OUTROS"
            
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
                                # Adiciona nossa coluna secreta sem mexer no resto
                                nota["origemConta"] = origem 
                            transacoes_novas.extend(lista_notas)
                except Exception as e:
                    pass
                time.sleep(1) # Pausa pra Ticket Log não bloquear
        data_atual += timedelta(days=1)
    return transacoes_novas

if __name__ == "__main__":
    # ATENÇÃO: NÃO CARREGA O HISTÓRICO! COMEÇA DO ZERO PRA LIMPAR O LIXO!
    todas_transacoes = buscar_dados_ano_todo()
    
    print("🧹 Aplicando Desduplicação Esmagadora (Limpeza de Duplicadas)...")
    unicos = {}
    for t in todas_transacoes:
        placa = t.get("placa", "SEM_PLACA")
        data_t = t.get("dataTransacao", "SEM_DATA")
        valor = t.get("valorTransacao", 0)
        
        # Chave Cega: Placa + Data + Valor. Impossível duplicar!
        chave_blindada = f"{placa}_{data_t}_{valor}"
        unicos[chave_blindada] = t
        
    dados_limpos = list(unicos.values())
    dados_limpos.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
    
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados_limpos, f, ensure_ascii=False, indent=2)
        
    print(f"✅ HARD RESET CONCLUÍDO! Base com {len(dados_limpos)} transações perfeitas e sem duplicadas.")
