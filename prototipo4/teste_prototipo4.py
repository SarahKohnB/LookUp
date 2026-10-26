
import torch
import cv2
from pathlib import Path

print("Carregando modelo...")

# Localiza o modelo dentro da pasta prototipo4
PASTA_ATUAL = Path(__file__).resolve().parent
CAMINHO_MODELO = PASTA_ATUAL / "prototipo4_ppe.pt"

print(f"Procurando modelo em: {CAMINHO_MODELO}")

if not CAMINHO_MODELO.is_file():
    raise FileNotFoundError(
        f"O arquivo do modelo não existe: {CAMINHO_MODELO}"
    )

modelo = torch.hub.load(
    "ultralytics/yolov5",
    "custom",
    path=str(CAMINHO_MODELO),
    force_reload=False
)

print("Modelo carregado!")

# Encontra o modelo na mesma pasta deste arquivo
PASTA_ATUAL = Path(__file__).resolve().parent
CAMINHO_MODELO = PASTA_ATUAL / "prototipo4_ppe.pt"

if not CAMINHO_MODELO.exists():
    raise FileNotFoundError(
        f"Modelo não encontrado: {CAMINHO_MODELO}"
    )

modelo = torch.hub.load(
    "ultralytics/yolov5",
    "custom",
    path=str(CAMINHO_MODELO),
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

# Define a resolução da webcam
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not camera.isOpened():
    print("Não foi possível abrir a webcam.")
    print("Verifique se a câmera está conectada ou tente o índice 0.")
    exit()

# Mostra a resolução utilizada
largura_camera = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
altura_camera = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Resolução da webcam: {largura_camera}x{altura_camera}")
print("Protótipo 4 iniciado!")
print("Pressione Q para fechar.")

try:
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

        # Painel de status dos EPIs
        altura, largura = imagem_resultado.shape[:2]

        painel_x = max(10, largura - 260)
        painel_y = 10
        painel_altura = 250

        cv2.rectangle(
            imagem_resultado,
            (painel_x, painel_y),
            (largura - 10, painel_y + painel_altura),
            (40, 40, 40),
            -1
        )

        cv2.rectangle(
            imagem_resultado,
            (painel_x, painel_y),
            (largura - 10, painel_y + painel_altura),
            (180, 180, 180),
            2
        )

        if pessoa_detectada:

            status_epis = {}

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

            for epi in epis_obrigatorios:

                if epi in epis_detectados:
                    status = "OK"
                    cor = (0, 255, 0)
                else:
                    status = "NAO DETECTADO"
                    cor = (0, 0, 255)

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

            # Cria o alerta
            if all(status == "OK" for status in status_epis.values()):
                tipo_alerta = "EPI COMPLETO"
                cor_alerta = (0, 255, 0)
            else:
                tipo_alerta = "EPI INCOMPLETO"
                cor_alerta = (0, 0, 255)

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

            # Status final na tela
            cv2.putText(
                imagem_resultado,
                tipo_alerta,
                (painel_x + 15, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                cor_alerta,
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

finally:
    camera.release()
    cv2.destroyAllWindows()
