import torch
import cv2

print("Carregando modelo...")

# Carrega o mesmo modelo utilizado no Protótipo 3
modelo = torch.hub.load(
    "ultralytics/yolov5",
    "custom",
    path="../prototipo3/prototipo3_ppe.pt",
    force_reload=False
)

print("Modelo carregado!")

# Confiança mínima para considerar uma detecção
CONF_MIN = 0.25

# EPIs que queremos verificar
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

print("Abrindo webcam...")

camera = cv2.VideoCapture(1)

if not camera.isOpened():
    print("Não foi possível abrir a webcam.")
    exit()

print("Protótipo 4 iniciado!")
print("Pressione Q para fechar.")

while True:

    sucesso, imagem = camera.read()

    if not sucesso:
        print("Não foi possível capturar a imagem.")
        break

    # Faz a detecção
    resultados = modelo(imagem)

    # Copia a imagem para desenhar os resultados
    imagem_resultado = imagem.copy()

    # Guarda os EPIs encontrados
    epis_detectados = set()

    pessoa_detectada = False

    # Percorre todas as detecções
    for *caixa, confianca, classe in resultados.xyxy[0].tolist():

        confianca = float(confianca)
        classe = int(classe)

        if confianca < CONF_MIN:
            continue

        nome = modelo.names[classe].lower()

        x1, y1, x2, y2 = map(int, caixa)

        # Verifica se encontrou uma pessoa
        if nome == "person":
            pessoa_detectada = True

        # Verifica se encontrou algum EPI
        if nome in epis_obrigatorios:
            epis_detectados.add(nome)

        # Desenha a caixa
        cv2.rectangle(
            imagem_resultado,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        # Nome e confiança
        nome_exibicao = nomes_epis.get(nome, nome)
        texto = f"{nome_exibicao} {confianca:.2f}"

        cv2.putText(
            imagem_resultado,
            texto,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    # --------------------------------
    # PAINEL DE STATUS DOS EPIs
    # --------------------------------

    altura, largura = imagem_resultado.shape[:2]

    # Área do painel
    painel_x = largura - 260
    painel_y = 10
    painel_largura = 250
    painel_altura = 250

    # Fundo do painel
    cv2.rectangle(
        imagem_resultado,
        (painel_x, painel_y),
        (largura - 10, painel_y + painel_altura),
        (40, 40, 40),
        -1
    )

    # Borda do painel
    cv2.rectangle(
        imagem_resultado,
        (painel_x, painel_y),
        (largura - 10, painel_y + painel_altura),
        (180, 180, 180),
        2
    )

    if pessoa_detectada:

        # Guarda o status de cada EPI
        status_epis = {}

        # Título
        cv2.putText(
            imagem_resultado,
            "STATUS DO EPI",
            (painel_x + 15, painel_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        y = painel_y + 60

        # Verifica cada EPI
        for epi in epis_obrigatorios:

            if epi in epis_detectados:
                status = "OK"
                cor = (0, 255, 0)
            else:
                status = "NAO DETECTADO"
                cor = (0, 0, 255)

            # Guarda o status para utilizar no alerta
            status_epis[epi] = status

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

        # --------------------------------
        # CRIA O ALERTA
        # --------------------------------

        if all(status == "OK" for status in status_epis.values()):
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

        # Mostra o alerta no terminal
        print(alerta)

        # --------------------------------
        # STATUS FINAL NA TELA
        # --------------------------------

        if tipo_alerta == "EPI COMPLETO":

            cv2.putText(
                imagem_resultado,
                "EPI COMPLETO",
                (painel_x + 15, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

        else:

            cv2.putText(
                imagem_resultado,
                "EPI INCOMPLETO",
                (painel_x + 15, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 0, 255),
                2
            )

    else:

        cv2.putText(
            imagem_resultado,
            "NENHUMA PESSOA",
            (painel_x + 15, painel_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2
        )

    # Mostra a imagem
    cv2.imshow(
        "Detector de EPI - Prototipo 4",
        imagem_resultado
    )

    # Tecla Q para fechar
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()