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
        texto = f"{nome} {confianca:.2f}"

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
    # VERIFICAÇÃO DOS EPIs
    # --------------------------------

    if pessoa_detectada:

        y = 30

        cv2.putText(
            imagem_resultado,
            "PESSOA DETECTADA",
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        y += 30

        # Verifica cada EPI
        for epi in epis_obrigatorios:

            if epi in epis_detectados:
                status = "OK"
            else:
                status = "NAO DETECTADO"

            texto = f"{epi}: {status}"

            cv2.putText(
                imagem_resultado,
                texto,
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0) if status == "OK" else (0, 0, 255),
                2
            )

            y += 25

        # Verifica se todos foram detectados
        if all(epi in epis_detectados for epi in epis_obrigatorios):

            cv2.putText(
                imagem_resultado,
                "EPI COMPLETO",
                (10, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

        else:

            cv2.putText(
                imagem_resultado,
                "EPI INCOMPLETO",
                (10, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

    else:

        cv2.putText(
            imagem_resultado,
            "NENHUMA PESSOA DETECTADA",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
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