
import cv2

def testar_camera():
    camera = None

    # Tenta abrir a webcam usando diferentes métodos.
    for indice in (0, 1, 2):
        for metodo in (cv2.CAP_DSHOW, cv2.CAP_MSMF):
            tentativa = cv2.VideoCapture(indice, metodo)

            if tentativa.isOpened():
                sucesso, imagem = tentativa.read()

                if sucesso and imagem is not None:
                    camera = tentativa
                    print(f"Webcam encontrada: câmera {indice}")
                    break

            tentativa.release()

        if camera is not None:
            break

    if camera is None:
        print("Não foi possível abrir a webcam.")
        print("Feche outros programas que estejam usando a câmera.")
        return

    print("Câmera funcionando!")
    print("Pressione Q para fechar o teste.")

    try:
        while True:
            sucesso, imagem = camera.read()

            if not sucesso or imagem is None:
                print("Não foi possível receber a imagem.")
                break

            cv2.imshow("Teste da webcam - SESI PE", imagem)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    testar_camera()
