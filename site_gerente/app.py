from flask import Flask, render_template, jsonify, redirect
from datetime import datetime

app = Flask(__name__)

# Guarda as notificações recebidas
notificacoes = []


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@app.route("/")
def pagina_inicial():

    return render_template(
        "index.html",
        notificacoes=notificacoes
    )


# ==========================================
# TESTE DE ALERTA
# ==========================================

@app.route("/teste-alerta")
def teste_alerta():

    notificacao = {
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tipo": "EPI INCOMPLETO",
        "capacete": "NAO DETECTADO",
        "colete": "OK",
        "luvas": "OK",
        "oculos": "OK",
        "mascara": "OK"
    }

    # Adiciona a nova notificação no começo da lista
    notificacoes.insert(0, notificacao)

    # Mantém somente as últimas 20 notificações
    if len(notificacoes) > 20:
        notificacoes.pop()

    return redirect("/")


# ==========================================
# API DAS NOTIFICAÇÕES
# ==========================================

@app.route("/notificacoes")
def obter_notificacoes():

    return jsonify(notificacoes)


# ==========================================
# INICIAR SITE
# ==========================================

if __name__ == "__main__":

    print("Site iniciado!")
    print("Acesse: http://127.0.0.1:5000")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )