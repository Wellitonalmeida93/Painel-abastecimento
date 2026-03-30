import requests
import json
import os
from datetime import datetime, timedelta
import time

# 🔹 CONFIGURAÇÕES DA TICKET LOG
URL = "https://srv1.ticketlog.com.br/ticketlog-servicos/ebs/transacaoVeiculo/search"
AUTHORIZATION = "Basic W09wZXJhZG9yV2ViXWFwcDEyMjg0MDQxOTg4OjExO1BTVG55"
CODIGO_CLIENTE = 122840
ARQUIVO_JSON = "transacoes.json"

def carregar_historico():
    # Verifica se o arquivo já existe no GitHub para não começar do zero
    if os.path.exists(ARQUIVO_JSON):
        try:
            with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao ler histórico: {e}")
    return []

def buscar_dados_recentes():
    print("🔄 Iniciando a busca na Ticket Log (Modo Inteligente Ninja)...")
    
    hoje = datetime.now()
    # Puxa APENAS os últimos 5 dias. Chega de buscar o ano todo!
    data_atual = hoje - timedelta(days=5)
    
    transacoes_novas = []
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }
    
    # ⏳ Loop super rápido de apenas 5 dias
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
                # Timeout gigante de 30 segundos mantido
                resp = requests.post(URL, json=payload, headers=headers, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("sucesso"):
                        transacoes_novas.extend(data.get("transacoes", []))
            except Exception as e:
                print(f"❌ Erro ao buscar dia {data_atual.strftime('%d/%m/%Y')}: {e}")
            
        data_atual += timedelta(days=1)
        # Pausa de 1 segundo para a Ticket Log não nos bloquear
        time.sleep(1) 
        
    return transacoes_novas

if __name__ == "__main__":
    # 1. Carrega o que já existe salvo no GitHub (O Histórico)
    dados_antigos = carregar_historico()
    print(f"📚 Histórico carregado: {len(dados_antigos)} transações antigas.")
    
    # 2. Busca só os últimos 5 dias
    dados_novos = buscar_dados_recentes()
    print(f"🆕 Novas transações encontradas nos últimos dias: {len(dados_novos)}")
    
    # 3. Junta tudo num panelão só
    todas_transacoes = dados_antigos + dados_novos
    
    # 4. A sua Desduplicação Implacável
    print("🧹 Aplicando Desduplicação Implacável...")
    unicos = {}
    for t in todas_transacoes:
        placa = t.get("placa", "SEM_PLACA")
        data_t = t.get("dataTransacao", "SEM_DATA")
        valor = t.get("valorTransacao", 0)
        
        chave_blindada = f"{placa}_{data_t}_{valor}"
        unicos[chave_blindada] = t
        
    dados_limpos = list(unicos.values())
    
    # Opcional: Garante que o arquivo salvo fique sempre ordenado do mais novo pro mais velho
    dados_limpos.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
    
    print(f"✅ Sucesso! Base blindada com {len(dados_limpos)} transações únicas no total.")
    
    # 5. Salva por cima do arquivo JSON
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados_limpos, f, ensure_ascii=False, indent=2)
        
    print("💾 Arquivo transacoes.json atualizado e pronto para o site!")
