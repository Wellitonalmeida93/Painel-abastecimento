from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# Serve o dashboard
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Serve o arquivo de dados para o JavaScript do index.html
@app.route('/transacoes.json')
def data():
    return send_from_directory('.', 'transacoes.json')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
