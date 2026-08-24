import torch
import cv2

print("Carregando modelo...")

modelo = torch.hub.load(
    "ultralytics/yolov5",
    "custom",
    path="prototipo3_ppe.pt",
    force_reload=False
)

print("Modelo carregado!")
print("Abrindo webcam...")

camera = cv2.VideoCapture(1)

if not camera.isOpened():
    print("Não foi possível abrir a webcam.")
    exit()

print("Protótipo 3 iniciado!")
print("Pressione Q para fechar.")

while True:
    sucesso, imagem = camera.read()

    if not sucesso:
        print("Não foi possível capturar a imagem.")
        break

    resultados = modelo(imagem)

    imagem_resultado = resultados.render()[0]

    cv2.imshow("Detector de EPI - Prototipo 3", imagem_resultado)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()