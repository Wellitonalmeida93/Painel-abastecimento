import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
import os

def disparar_briefing_diretoria():
    arquivo_json = "transacoes.json"
    
    if not os.path.exists(arquivo_json):
        print("Arquivo JSON não encontrado. E-mail cancelado.")
        return

    try:
        with open(arquivo_json, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except Exception as e:
        print("Erro ao ler JSON:", e)
        return

    # Definir datas
    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)
    str_ontem = ontem.strftime("%Y-%m-%d")
    
    # KPIs
    gasto_total = 0
    economia = 0
    fugas = 0
    
    for t in dados:
        if str_ontem in t.get("dataTransacao", ""):
            gasto_total += float(t.get("valorTransacao", 0))
            perda = float(t.get("perda_total", 0))
            if perda < 0:
                economia += abs(perda)
            elif perda > 0:
                fugas += perda

    resultado = economia - fugas
    cor = "#10b981" if resultado >= 0 else "#ef4444"
    txt_resultado = "SAVING LÍQUIDO" if resultado >= 0 else "FUGA LÍQUIDA"

    # Construção do HTML do E-mail
    html_email = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f1f5f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 12px; border-top: 4px solid #8b5cf6; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h2 style="color: #0f172a; margin-top: 0;">📊 Briefing Executivo de Abastecimento</h2>
            <p style="color: #64748b; font-size: 14px;">Resultados de {ontem.strftime('%d/%m/%Y')}</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <tr>
                    <td style="padding: 15px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px 0 0 8px;">
                        <span style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: bold;">Custo Total Operado</span><br>
                        <span style="font-size: 22px; font-weight: bold; color: #0f172a;">R$ {gasto_total:,.2f}</span>
                    </td>
                    <td style="padding: 15px; background: {cor}10; border: 1px solid {cor}40; border-radius: 0 8px 8px 0;">
                        <span style="font-size: 11px; color: {cor}; text-transform: uppercase; font-weight: bold;">{txt_resultado}</span><br>
                        <span style="font-size: 22px; font-weight: bold; color: {cor};">R$ {abs(resultado):,.2f}</span>
                    </td>
                </tr>
            </table>

            <div style="margin-top: 30px; padding: 15px; background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 4px;">
                <h4 style="margin: 0 0 5px 0; color: #b91c1c;">⚠️ Resumo de Fugas (Postos sem acordo)</h4>
                <p style="margin: 0; font-size: 13px; color: #7f1d1d;">Ontem registramos R$ {fugas:,.2f} em fugas de negociação. Verifique o painel para auditar as placas e postos reincidentes.</p>
            </div>
            
            <div style="margin-top: 40px; text-align: center;">
                <!-- SUBSTITUA AQUI PELO LINK REAL DO SEU PAINEL NO GITHUB PAGES OU SERVIDOR -->
                <a href="https://seu-link-do-painel-aqui.com" style="background: #0f172a; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Acessar Dashboard Completo</a>
            </div>
        </div>
      </body>
    </html>
    """

    # Configuração de Envio via Gmail
    remetente = "SEU_EMAIL@gmail.com"  # COLOQUE SEU E-MAIL AQUI
    senha = "SUA_SENHA_DE_APLICATIVO"  # COLOQUE SUA SENHA DE APP AQUI
    destinatario = "DIRETOR@EMPRESA.COM" # COLOQUE O E-MAIL DO DIRETOR AQUI

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Abastecimento Diário: {txt_resultado} de R$ {abs(resultado):,.2f}"
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.attach(MIMEText(html_email, "html"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(remetente, senha)
        server.sendmail(remetente, destinatario, msg.as_string())
        server.quit()
        print("✅ E-mail diário disparado com sucesso para a diretoria!")
    except Exception as e:
        print("❌ Erro ao disparar e-mail:", e)

if __name__ == "__main__":
    disparar_briefing_diretoria()
