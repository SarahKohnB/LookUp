from ultralytics import YOLO
import cv2

# Carrega o modelo YOLO
modelo = YOLO("yolo11n.pt")

# Abre a webcam externa
camera = cv2.VideoCapture(1)

# Verifica se a câmera abriu
if not camera.isOpened():
    print("Não foi possível abrir a webcam externa.")
    exit()

print("YOLO iniciado!")
print("Pressione Q para fechar.")

while True:
    # Captura uma imagem da webcam
    sucesso, imagem = camera.read()

    if not sucesso:
        print("Não foi possível capturar a imagem.")
        break

    # Analisa a imagem
    resultados = modelo(imagem, verbose=False)

    # Desenha as caixas e os nomes detectados
    imagem_com_deteccoes = resultados[0].plot()

    # Mostra o vídeo
    cv2.imshow(
        "Detector de EPI - Teste YOLO",
        imagem_com_deteccoes
    )

    # Fecha ao apertar Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Fecha a câmera
camera.release()
cv2.destroyAllWindows()