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
            print(f"⚠️ Erro ao ler histórico: {e}")
    return []

def buscar_dados_recentes():
    print("🔄 Iniciando a busca na Ticket Log (MODO LEVE DE 5 DIAS)...")
    
    hoje = datetime.now()
    # 🔥 AQUI ESTÁ A MUDANÇA: Volta apenas 5 dias no passado! 🔥
    data_atual = hoje - timedelta(days=5)
    
    transacoes_novas = []
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTHORIZATION
    }
    
    # ⏳ Loop de datas
    while data_atual <= hoje:
        inicio = data_atual.strftime("%Y-%m-%dT00:00:00")
        fim = data_atual.strftime("%Y-%m-%dT23:59:59")
        
        print(f"   📅 Consultando dia {data_atual.strftime('%d/%m/%Y')}...")
        
        # 🔥 LOOP DE CLIENTES
        for cliente in CODIGOS_CLIENTES:
            
            # 🏷️ Define o carimbo
            if cliente == 122840:
                tipo_frota = "FROTA"
            elif cliente == 206518:
                tipo_frota = "AGREGADO"
            else:
                tipo_frota = "OUTROS"
            
            for considerar in ["V", "T"]:
                payload = {
                    "codigoCliente": cliente,
                    "codigoTipoCartao": 4,
                    "dataTransacaoInicial": inicio,
                    "dataTransacaoFinal": fim,
                    "considerarTransacao": considerar,
                    "ordem": "S",
                    "validacao": "S"
                }
                
                try:
                    resp = requests.post(URL, json=payload, headers=headers, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("sucesso"):
                            lista_notas = data.get("transacoes", [])
                            
                            # 🔥 CARIMBANDO AS NOTAS NOVAS 🔥
                            for nota in lista_notas:
                                nota["tipoFrota"] = tipo_frota
                                
                            transacoes_novas.extend(lista_notas)
                except Exception as e:
                    print(f"❌ Erro ao buscar dia {data_atual.strftime('%d/%m/%Y')} (Cliente {cliente}): {e}")
                
                # Pausa de 1 segundo para não sobrecarregar
                time.sleep(1) 
            
        data_atual += timedelta(days=1)
        
    return transacoes_novas

if __name__ == "__main__":
    # Carrega o arquivão gigante que você já subiu pro GitHub
    dados_antigos = carregar_historico()
    print(f"📚 Histórico carregado: {len(dados_antigos)} transações antigas.")
    
    # Busca apenas os últimos 5 dias para atualizar as frotas
    dados_novos = buscar_dados_recentes()
    print(f"🆕 Novas transações encontradas: {len(dados_novos)}")
    
    # Junta tudo 
    todas_transacoes = dados_antigos + dados_novos
    
    print("🧹 Aplicando Desduplicação Implacável...")
    unicos = {}
    for t in todas_transacoes:
        placa = t.get("placa", "SEM_PLACA")
        data_t = t.get("dataTransacao", "SEM_DATA")
        valor = t.get("valorTransacao", 0)
        empresa = t.get("tipoFrota", "SEM_EMPRESA")
        
        # A chave agora inclui a empresa pra evitar conflitos raros
        chave_blindada = f"{placa}_{data_t}_{valor}_{empresa}"
        unicos[chave_blindada] = t
        
    dados_limpos = list(unicos.values())
    
    # Ordena do mais novo pro mais velho
    dados_limpos.sort(key=lambda x: x.get("dataTransacao", ""), reverse=True)
    
    print(f"✅ ATUALIZAÇÃO LEVE CONCLUÍDA! Base com {len(dados_limpos)} transações unificadas.")
    
    # Salva o arquivo no ambiente do GitHub
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados_limpos, f, ensure_ascii=False, indent=2)
        
    print("💾 Arquivo transacoes.json atualizado no GitHub!")
