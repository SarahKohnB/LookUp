import cv2

# Abre a webcam externa
camera = cv2.VideoCapture(1)

# Verifica se a webcam abriu
if not camera.isOpened():
    print("Não foi possível abrir a webcam externa.")
    exit()

print("Webcam externa aberta!")
print("Pressione Q para fechar.")

while True:
    # Captura a imagem da webcam
    sucesso, imagem = camera.read()

    # Verifica se conseguiu capturar a imagem
    if not sucesso:
        print("Não foi possível capturar a imagem.")
        break

    # Mostra a imagem da webcam
    cv2.imshow("Câmera - Detector de EPI", imagem)

    # Fecha a câmera ao apertar Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Libera a webcam
camera.release()

# Fecha as janelas
cv2.destroyAllWindows()