from ultralytics import YOLO
import cv2

# Carrega o novo modelo de EPI
modelo = YOLO("modelos/prototipo2_ppe.pt")

# Abre a webcam externa
camera = cv2.VideoCapture(1)

if not camera.isOpened():
    print("Não foi possível abrir a webcam externa.")
    exit()

print("Protótipo 2 iniciado!")
print("Pressione Q para fechar.")

while True:
    sucesso, imagem = camera.read()

    if not sucesso:
        print("Não foi possível capturar a imagem.")
        break

    # Detecta os EPIs
    resultados = modelo(imagem, conf=0.25, verbose=False)

    # Desenha as caixas e nomes
    imagem_resultado = resultados[0].plot()

    # Mostra a câmera
    cv2.imshow("Detector de EPI - Prototipo 2", imagem_resultado)

    # Q fecha a câmera
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()