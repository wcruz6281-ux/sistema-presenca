
import cv2
import json
import urllib.request
import urllib.error
import time
from pathlib import Path

# =========================
# CONFIGURACOES
# =========================

MODELO = Path("modelo_rosto.yml")

URL_ALUNOS = "http://127.0.0.1:8000/alunos"
URL_PRESENCA = "http://127.0.0.1:8000/presencas/registrar"

LIMITE_DISTANCIA = 60
TEMPO_ENTRE_TENTATIVAS = 10

ultima_tentativa = {}
presencas_confirmadas = set()
rostos_exibidos = set()


# =========================
# REGISTRO DE PRESENCA
# =========================

def registrar_presenca(aluno_id):
    dados = json.dumps({
        "aluno_id": int(aluno_id)
    }).encode("utf-8")

    requisicao = urllib.request.Request(
        URL_PRESENCA,
        data=dados,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            requisicao, timeout=5
        ) as resposta:
            resultado = json.loads(
                resposta.read().decode("utf-8")
            )

        mensagem = resultado.get(
            "mensagem", "Solicitação concluída."
        )
        nome = resultado.get(
            "aluno", f"ID {aluno_id}"
        )

        if resultado.get("duplicada"):
            print(
                f"\n[JÁ REGISTRADA] {nome}: {mensagem}",
                flush=True
            )
        else:
            print(
                f"\n[PRESENÇA REGISTRADA] {nome}: {mensagem}",
                flush=True
            )

        return True

    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode(
            "utf-8", errors="replace"
        )
        print(
            f"\n[ERRO HTTP {erro.code}] {detalhe}",
            flush=True
        )

    except urllib.error.URLError as erro:
        print(
            "\n[ERRO DE CONEXÃO] Confira se o "
            f"servidor está ligado: {erro}",
            flush=True
        )

    except Exception as erro:
        print(
            f"\n[ERRO] Não foi possível registrar: {erro}",
            flush=True
        )

    return False


# =========================
# VERIFICACOES INICIAIS
# =========================

if not MODELO.exists():
    print("Modelo não encontrado.")
    print("Execute treinar_rosto.py primeiro.")
    raise SystemExit

try:
    with urllib.request.urlopen(
        URL_ALUNOS, timeout=5
    ) as resposta:
        alunos = json.loads(
            resposta.read().decode("utf-8")
        )

    nomes = {
        int(aluno["id"]): aluno["nome"]
        for aluno in alunos
        if aluno.get("ativo", True)
    }

    if not nomes:
        print("Nenhum aluno ativo foi encontrado.")
        raise SystemExit

except Exception as erro:
    print("Não foi possível consultar os alunos.")
    print("Confira se o servidor FastAPI está ligado.")
    print(f"Detalhe: {erro}")
    raise SystemExit


# =========================
# RECONHECIMENTO FACIAL
# =========================

classificador = cv2.CascadeClassifier(
    cv2.data.haarcascades
    + "haarcascade_frontalface_default.xml"
)

if classificador.empty():
    print("Erro ao carregar o classificador de rostos.")
    raise SystemExit

reconhecedor = cv2.face.LBPHFaceRecognizer_create()
reconhecedor.read(str(MODELO))

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("Erro: não foi possível abrir a webcam.")
    raise SystemExit

print("=" * 50, flush=True)
print(" SISTEMA DE PRESENÇA INICIADO", flush=True)
print(" Aproxime-se da câmera.", flush=True)
print(" Pressione Q para sair.", flush=True)
print("=" * 50, flush=True)


# =========================
# LOOP PRINCIPAL
# =========================

try:
    while True:
        ok, frame = camera.read()

        if not ok:
            print(
                "Erro ao capturar imagem da câmera.",
                flush=True
            )
            time.sleep(0.2)
            continue

        cinza = cv2.cvtColor(
            frame, cv2.COLOR_BGR2GRAY
        )

        rostos = classificador.detectMultiScale(
            cinza,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80)
        )

        agora = time.monotonic()

        for (x, y, w, h) in rostos:
            rosto = cinza[y:y + h, x:x + w]
            rosto = cv2.resize(rosto, (200, 200))

            identificacao, distancia = reconhecedor.predict(
                rosto
            )

            if (
                identificacao in nomes
                and distancia < LIMITE_DISTANCIA
            ):
                nome = nomes[identificacao]

                texto = f"{nome} (ID {identificacao})"
                cor = (0, 200, 0)

                # Exibe a mensagem somente uma vez
                # por aluno durante esta execução.
                if identificacao not in rostos_exibidos:
                    print(
                        f"\n[ROSTO RECONHECIDO] {nome} "
                        f"| ID: {identificacao} "
                        f"| Distância: {distancia:.1f}",
                        flush=True
                    )
                    rostos_exibidos.add(identificacao)

                ultima = ultima_tentativa.get(
                    identificacao, 0
                )

                # Evita novas tentativas após a API
                # confirmar a presença.
                if identificacao not in presencas_confirmadas:
                    if (
                        agora - ultima
                        >= TEMPO_ENTRE_TENTATIVAS
                    ):
                        ultima_tentativa[identificacao] = agora

                        sucesso = registrar_presenca(
                            identificacao
                        )

                        if sucesso:
                            presencas_confirmadas.add(
                                identificacao
                            )

            else:
                texto = f"Não reconhecido ({distancia:.1f})"
                cor = (0, 0, 255)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                cor,
                2
            )

            cv2.putText(
                frame,
                texto,
                (x, max(y - 10, 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                cor,
                2
            )

        cv2.imshow(
            "Reconhecimento facial - Sistema de Presenca",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    cv2.destroyAllWindows()
    print(
        "\nSistema de reconhecimento encerrado.",
        flush=True
    )
