import requests
import json
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES DA TICKET LOG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840

def buscar_dados_mes():
    print("🔄 Iniciando a busca de dados na Ticket Log (Modo Robô)...")
    
    hoje = datetime.now()
    # Pega o dia 1º de Janeiro do ano atual (assim funciona para 2026, 2027...)
    inicio_ano = hoje.replace(month=1, day=1) 
    data_atual = inicio_ano
    
    todas_transacoes = []
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }
    
    # ⏳ Loop tranquilo: dia por dia, do dia 1 até hoje
    while data_atual <= hoje:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")
        
        print(f"   📅 Consultando dia {data_atual.strftime('%d/%m/%Y')}...")
        
        for considerar in ["V", "T"]:
            payload = {
                "codigoCliente": CODIGO_CLIENTE,
                "codigoTipoCartao": 4,
                "dataTransacaoInicial": inicio,
                "dataTransacaoFinal": fim,
                "considerarTransacao": considerar,
                "ordem": "S",
                "validacao": "S"
            }
            
            try:
                # Timeout gigante de 30 segundos, pois o GitHub não tem pressa
                resp = requests.post(URL, json=payload, headers=headers, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("sucesso"):
                        todas_transacoes.extend(data.get("transacoes", []))
            except Exception as e:
                print(f"❌ Erro ao buscar dia {data_atual.strftime('%d/%m/%Y')}: {e}")
                
        data_atual += timedelta(days=1)
        # Pausa de 1 segundo para a Ticket Log não bloquear nosso robô
        time.sleep(1) 
        
    print("🧹 Aplicando Desduplicação Implacável...")
    unicos = {}
    for t in todas_transacoes:
        placa = t.get("placa", "SEM_PLACA")
        data_t = t.get("dataTransacao", "SEM_DATA")
        valor = t.get("valorTransacao", 0)
        
        chave_blindada = f"{placa}_{data_t}_{valor}"
        unicos[chave_blindada] = t
        
    dados_limpos = list(unicos.values())
    print(f"✅ Sucesso! {len(dados_limpos)} transações válidas encontradas.")
    
    return dados_limpos

if __name__ == "__main__":
    # 1. Puxa os dados
    dados = buscar_dados_mes()
    
    # 2. Salva por cima do seu arquivo transacoes.json atual
    with open("transacoes.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        
    print("💾 Arquivo transacoes.json atualizado e pronto para o site!")
