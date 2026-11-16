
from flask import (
    Flask, render_template, render_template_string,
    jsonify, redirect, Response, request, session, url_for
)
from pathlib import Path
from datetime import datetime
from collections import deque
from functools import wraps
import threading
import time

import torch
import cv2

app = Flask(__name__)
app.secret_key = "look-up-chave-escolar-trocar-depois"

USUARIO_GERENTE = "gerente"
SENHA_GERENTE = "123456"

# ==========================================
# LOGIN
# ==========================================

def login_obrigatorio(funcao):
    @wraps(funcao)
    def verificar_login(*args, **kwargs):
        if not session.get("gerente_logado"):
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)
    return verificar_login


# ==========================================
# CONFIGURACOES
# ==========================================

CONF_MIN = 0.25
INDICE_CAMERA = 1
PORTA = 5000

TAMANHO_JANELA = 8
MINIMO_DETECCOES = 3

PASTA_PROJETO = Path(__file__).resolve().parent.parent

CAMINHO_MODELO = (
    PASTA_PROJETO / "prototipo4" / "prototipo4_ppe.pt"
)

epis_obrigatorios = [
    "helmet",
    "vest",
    "gloves",
    "glasses",
    "mask"
]

nomes_epis = {
    "helmet": "Capacete",
    "vest": "Colete",
    "gloves": "Luvas",
    "glasses": "Oculos",
    "mask": "Mascara"
}

apelidos = {
    "hard-hat": "helmet",
    "hard_hat": "helmet",
    "safety-helmet": "helmet",
    "safety-vest": "vest",
    "safety_vest": "vest",
    "glove": "gloves",
    "safety-glasses": "glasses",
    "safety_glasses": "glasses",
    "goggles": "glasses",
    "eye-protection": "glasses",
    "face-mask": "mask",
    "face_mask": "mask",
    "surgical-mask": "mask"
}

# ==========================================
# DADOS COMPARTILHADOS
# ==========================================

notificacoes = []
trava = threading.Lock()
ultimo_frame = None

status_atual = {
    "camera_online": False,
    "pessoa_detectada": False,
    "tipo": "AGUARDANDO CAMERA",
    "epis": {
        epi: "AGUARDANDO"
        for epi in epis_obrigatorios
    }
}


# ==========================================
# NOTIFICACOES
# ==========================================

def adicionar_notificacao(alerta):
    notificacao = {
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tipo": alerta["tipo"],
        "capacete": alerta["capacete"],
        "colete": alerta["colete"],
        "luvas": alerta["luvas"],
        "oculos": alerta["oculos"],
        "mascara": alerta["mascara"]
    }

    with trava:
        notificacoes.insert(0, notificacao)
        del notificacoes[20:]


def normalizar_nome(nome):
    nome = str(nome).lower().strip()
    return apelidos.get(nome, nome)


# ==========================================
# PROCESSAMENTO DA WEBCAM
# ==========================================

def processar_camera():
    global ultimo_frame, status_atual

    if not CAMINHO_MODELO.is_file():
        print(f"ERRO: modelo nao encontrado: {CAMINHO_MODELO}")

        with trava:
            status_atual["tipo"] = "MODELO NAO ENCONTRADO"

        return

    print("Carregando modelo YOLO...")

    try:
        modelo = torch.hub.load(
            "ultralytics/yolov5",
            "custom",
            path=str(CAMINHO_MODELO),
            force_reload=False
        )

        print("Classes encontradas no modelo:", modelo.names)

    except Exception as erro:
        print(f"Erro ao carregar o modelo: {erro}")

        with trava:
            status_atual["tipo"] = "ERRO AO CARREGAR MODELO"

        return

    print("Modelo carregado!")
    print("Abrindo webcam...")

    camera = cv2.VideoCapture(INDICE_CAMERA)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not camera.isOpened():
        print("ERRO: nao foi possivel abrir a webcam.")

        with trava:
            status_atual["tipo"] = "CAMERA INDISPONIVEL"
            status_atual["camera_online"] = False

        camera.release()
        return

    print("Webcam conectada!")

    historico_epis = deque(maxlen=TAMANHO_JANELA)

    # Guarda o ultimo estado registrado no historico.
    ultimo_alerta_emitido = None

    try:
        while True:
            sucesso, imagem = camera.read()

            if not sucesso:
                time.sleep(0.1)
                continue

            resultados = modelo(imagem)
            imagem_resultado = imagem.copy()

            epis_detectados = set()
            pessoa_detectada = False

            # ----------------------------------
            # LEITURA DAS DETECCOES
            # ----------------------------------

            for *caixa, confianca, classe in resultados.xyxy[0].tolist():

                confianca = float(confianca)
                classe = int(classe)

                if confianca < CONF_MIN:
                    continue

                nome_original = modelo.names[classe]
                nome = normalizar_nome(nome_original)

                x1, y1, x2, y2 = map(int, caixa)

                if nome == "person":
                    pessoa_detectada = True

                if nome in epis_obrigatorios:
                    epis_detectados.add(nome)

                nome_exibicao = nomes_epis.get(
                    nome, str(nome_original)
                )

                texto = f"{nome_exibicao} {confianca:.2f}"

                cv2.rectangle(
                    imagem_resultado,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    imagem_resultado,
                    texto,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            # ----------------------------------
            # ESTABILIZACAO DAS DETECCOES
            # ----------------------------------

            if pessoa_detectada:
                historico_epis.append(epis_detectados.copy())
            else:
                historico_epis.append(set())

            status_epis = {}

            if pessoa_detectada:

                for epi in epis_obrigatorios:
                    quantidade = sum(
                        1 for quadro in historico_epis
                        if epi in quadro
                    )

                    if quantidade >= MINIMO_DETECCOES:
                        status_epis[epi] = "OK"
                    else:
                        status_epis[epi] = "NAO DETECTADO"

                if all(
                    status_epis[epi] == "OK"
                    for epi in epis_obrigatorios
                ):
                    tipo_alerta = "EPI COMPLETO"
                else:
                    tipo_alerta = "EPI INCOMPLETO"

                alerta = {
                    "tipo": tipo_alerta,
                    "capacete": status_epis["helmet"],
                    "colete": status_epis["vest"],
                    "luvas": status_epis["gloves"],
                    "oculos": status_epis["glasses"],
                    "mascara": status_epis["mask"]
                }

                # Registra somente quando muda entre completo
                # e incompleto. Evita repetir o mesmo aviso.
                if tipo_alerta != ultimo_alerta_emitido:
                    adicionar_notificacao(alerta)

                    print(
                        "Mudanca de status registrada:",
                        alerta
                    )

                    ultimo_alerta_emitido = tipo_alerta

            else:
                tipo_alerta = "NENHUMA PESSOA"

                status_epis = {
                    epi: "AGUARDANDO"
                    for epi in epis_obrigatorios
                }

                # Permite registrar uma nova ocorrencia
                # quando uma pessoa voltar a ser detectada.
                ultimo_alerta_emitido = None

            # ----------------------------------
            # PAINEL NA IMAGEM
            # ----------------------------------

            altura, largura = imagem_resultado.shape[:2]

            painel_x = max(10, largura - 270)
            painel_y = 10

            cv2.rectangle(
                imagem_resultado,
                (painel_x, painel_y),
                (largura - 10, painel_y + 270),
                (40, 40, 40),
                -1
            )

            cv2.putText(
                imagem_resultado,
                "STATUS DO EPI",
                (painel_x + 15, painel_y + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            y = painel_y + 65

            for epi in epis_obrigatorios:
                status = status_epis[epi]

                if status == "OK":
                    cor = (0, 255, 0)
                elif status == "NAO DETECTADO":
                    cor = (0, 0, 255)
                else:
                    cor = (0, 255, 255)

                texto = f"{nomes_epis[epi]}: {status}"

                cv2.putText(
                    imagem_resultado,
                    texto,
                    (painel_x + 15, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.48,
                    cor,
                    2
                )

                y += 30

            if tipo_alerta == "EPI COMPLETO":
                cor_final = (0, 255, 0)
            elif tipo_alerta == "EPI INCOMPLETO":
                cor_final = (0, 0, 255)
            else:
                cor_final = (0, 255, 255)

            cv2.putText(
                imagem_resultado,
                tipo_alerta,
                (painel_x + 15, painel_y + 250),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                cor_final,
                2
            )

            # ----------------------------------
            # ENVIO DA IMAGEM PARA O SITE
            # ----------------------------------

            sucesso_jpeg, buffer = cv2.imencode(
                ".jpg",
                imagem_resultado,
                [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            )

            if sucesso_jpeg:
                with trava:
                    ultimo_frame = buffer.tobytes()

                    status_atual = {
                        "camera_online": True,
                        "pessoa_detectada": pessoa_detectada,
                        "tipo": tipo_alerta,
                        "epis": status_epis.copy()
                    }

    except Exception as erro:
        print(f"Erro durante o processamento da camera: {erro}")

    finally:
        camera.release()
        print("Webcam desconectada.")


# ==========================================
# VIDEO PARA O NAVEGADOR
# ==========================================

def gerar_video():
    while True:
        with trava:
            quadro = ultimo_frame

        if quadro is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + quadro
                + b"\r\n"
            )

        time.sleep(0.03)


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = ""

    if session.get("gerente_logado"):
        return redirect(url_for("pagina_inicial"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        if usuario == USUARIO_GERENTE and senha == SENHA_GERENTE:
            session["gerente_logado"] = True
            return redirect(url_for("pagina_inicial"))

        erro = "Usuário ou senha incorretos."

    return render_template_string('''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Look Up</title>
    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
            background: #f2edfb;
            color: #29213a;
        }

        .caixa {
            width: 90%;
            max-width: 360px;
            background: white;
            padding: 32px;
            border-radius: 14px;
            box-shadow: 0 8px 28px #25104418;
        }

        h1 {
            text-align: center;
            color: #7041ad;
            margin: 0 0 8px;
        }

        .subtitulo {
            text-align: center;
            color: #777;
            margin: 0 0 26px;
        }

        label {
            display: block;
            margin: 14px 0 6px;
            font-weight: bold;
        }

        input {
            width: 100%;
            padding: 12px;
            border: 1px solid #d8d0e4;
            border-radius: 7px;
            font-size: 15px;
        }

        button {
            width: 100%;
            margin-top: 22px;
            padding: 12px;
            border: 0;
            border-radius: 7px;
            background: #7041ad;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }

        button:hover {
            background: #59328d;
        }

        .erro {
            color: #c62828;
            text-align: center;
            margin-top: 14px;
        }

        .rodape {
            text-align: center;
            color: #777;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <form class="caixa" method="POST">
        <h1>LOOK UP</h1>
        <p class="subtitulo">Monitoramento de EPIs</p>

        <label for="usuario">Usuário</label>
        <input
            id="usuario"
            name="usuario"
            type="text"
            placeholder="Digite seu usuário"
            required
            autofocus
        >

        <label for="senha">Senha</label>
        <input
            id="senha"
            name="senha"
            type="password"
            placeholder="Digite sua senha"
            required
        >

        <button type="submit">Entrar</button>

        {% if erro %}
            <p class="erro">{{ erro }}</p>
        {% endif %}

        <p class="rodape">Acesso restrito ao gerente</p>
    </form>
</body>
</html>
''', erro=erro)


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


# ==========================================
# VIDEO PROTEGIDO
# ==========================================

@app.route("/video_feed")
@login_obrigatorio
def video_feed():
    return Response(
        gerar_video(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ==========================================
# PAGINA PRINCIPAL
# ==========================================

@app.route("/")
@login_obrigatorio
def pagina_inicial():
    with trava:
        lista = notificacoes.copy()

    return render_template(
        "index.html",
        notificacoes=lista
    )


# ==========================================
# STATUS ATUAL DOS EPIs
# ==========================================

@app.route("/api/status")
@login_obrigatorio
def obter_status():
    with trava:
        dados = {
            "camera_online": status_atual["camera_online"],
            "pessoa_detectada": status_atual["pessoa_detectada"],
            "tipo": status_atual["tipo"],
            "epis": status_atual["epis"].copy()
        }

    return jsonify(dados)


# ==========================================
# NOTIFICACOES
# ==========================================

@app.route("/notificacoes")
@login_obrigatorio
def obter_notificacoes():
    with trava:
        dados = notificacoes.copy()

    return jsonify(dados)


# ==========================================
# INICIAR SERVIDOR
# ==========================================

if __name__ == "__main__":
    print("Iniciando sistema LookUp...")

    thread_detector = threading.Thread(
        target=processar_camera,
        daemon=True
    )
    thread_detector.start()

    print("\n===================================")
    print("          SISTEMA LOOK UP")
    print("===================================")
    print("TELA DE LOGIN:")
    print(f"http://127.0.0.1:{PORTA}/login")
    print("===================================\n")

    app.run(
        host="0.0.0.0",
        port=PORTA,
        debug=False,
        threaded=True
    )