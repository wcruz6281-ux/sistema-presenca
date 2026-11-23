
import cv2

def main():
    # Detector de rostos incluído no OpenCV
    arquivo = cv2.data.haarcascades + (
        "haarcascade_frontalface_default.xml"
    )

    detector = cv2.CascadeClassifier(arquivo)

    if detector.empty():
        print("Não foi possível carregar o detector de rostos.")
        return

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Não foi possível abrir a webcam.")
        return

    print("Detecção iniciada. Pressione Q para sair.")

    try:
        while True:
            sucesso, imagem = camera.read()

            if not sucesso:
                print("Não foi possível ler a imagem.")
                break

            cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

            rostos = detector.detectMultiScale(
                cinza,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(60, 60)
            )

            for (x, y, largura, altura) in rostos:
                cv2.rectangle(
                    imagem,
                    (x, y),
                    (x + largura, y + altura),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    imagem,
                    "Rosto detectado",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

            cv2.imshow("Sistema de Presenca - Teste", imagem)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
