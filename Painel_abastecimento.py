import pandas as pd
import json
import requests
import os

# URL da sua planilha publicada como Excel
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTMrknZbVmnLdLOW4knDIW4Wmjw6CMUyttdpw1c4SnxJP9HjmQcsH0heNOShzOrdHsOs7MDQuhZazcI/pub?output=xlsx"

def atualizar_dados():
    try:
        print("🔄 Baixando dados da Planilha Google...")
        # Lendo o Excel diretamente da URL
        df = pd.read_excel(URL_PLANILHA)
        
        # Opcional: Tratar nomes de colunas se necessário (remover espaços, etc)
        # df.columns = df.columns.str.strip()

        # Converte para lista de dicionários (formato JSON)
        dados = df.to_dict(orient="records")
        
        # Salva o arquivo que o Dashboard utiliza
        with open("transacoes.json", "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Sucesso! {len(dados)} linhas processadas.")
    except Exception as e:
        print(f"❌ Erro ao atualizar: {e}")

if __name__ == "__main__":
    atualizar_dados()
