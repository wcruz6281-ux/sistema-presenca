
import cv2
import json
import urllib.request
from pathlib import Path

# Pasta separada para os rostos dos alunos.
# As imagens antigas de rostos_teste serão preservadas.
PASTA_BASE = Path("rostos_alunos")
PASTA_BASE.mkdir(exist_ok=True)

URL_ALUNOS = "http://127.0.0.1:8000/alunos"

# Busca os alunos que já estão cadastrados no sistema.
try:
    with urllib.request.urlopen(URL_ALUNOS, timeout=5) as resposta:
        alunos = json.loads(resposta.read().decode("utf-8"))
except Exception as erro:
    print("Não consegui acessar a lista de alunos.")
    print("Confira se o servidor está rodando.")
    print(f"Detalhes: {erro}")
    raise SystemExit

if not alunos:
    print("Não há alunos cadastrados no sistema.")
    raise SystemExit

print("\n=== ALUNOS CADASTRADOS ===")
for aluno in alunos:
    print(
        f"ID: {aluno['id']} | "
        f"Nome: {aluno['nome']} | "
        f"Matrícula: {aluno['matricula']}"
    )

try:
    aluno_id = int(input("\nDigite o ID do aluno autorizado: "))
except ValueError:
    print("ID inválido. Digite um número.")
    raise SystemExit

aluno = next(
    (a for a in alunos if a["id"] == aluno_id),
    None
)

if aluno is None:
    print("Esse ID não foi encontrado no sistema.")
    raise SystemExit

# Cada aluno terá sua própria pasta.
pasta_aluno = PASTA_BASE / f"aluno_{aluno_id}"
pasta_aluno.mkdir(parents=True, exist_ok=True)

# Continua a numeração sem sobrescrever imagens existentes.
existentes = list(pasta_aluno.glob("rosto_*.png"))
contador = len(existentes)
limite = 30

if contador >= limite:
    print("Esse aluno já possui 30 ou mais imagens.")
    print("Nenhuma imagem foi alterada.")
    raise SystemExit

classificador = cv2.CascadeClassifier(
    cv2.data.haarcascades
    + "haarcascade_frontalface_default.xml"
)

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("Erro: não foi possível abrir a webcam.")
    raise SystemExit

print(f"\nCadastro facial: {aluno['nome']}")
print("Use somente com autorização adequada.")
print("Olhe para a câmera e pressione ESPAÇO para capturar.")
print("Pressione Q para sair.")

try:
    while contador < limite:
        ok, frame = camera.read()

        if not ok:
            print("Não foi possível ler a imagem da câmera.")
            break

        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostos = classificador.detectMultiScale(
            cinza,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80)
        )

        for (x, y, w, h) in rostos:
            cv2.rectangle(
                frame, (x, y), (x + w, y + h),
                (0, 255, 0), 2
            )

        cv2.putText(
            frame,
            f"{aluno['nome']} - Imagens: {contador}/{limite}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

        cv2.imshow("Cadastro facial por aluno", frame)
        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            break

        if tecla == 32 and len(rostos) > 0:
            x, y, w, h = max(
                rostos, key=lambda r: r[2] * r[3]
            )

            rosto = cinza[y:y + h, x:x + w]
            rosto = cv2.resize(rosto, (200, 200))

            numero = contador + 1
            caminho = pasta_aluno / f"rosto_{numero:03d}.png"

            if cv2.imwrite(str(caminho), rosto):
                contador += 1
                print(f"Imagem salva: {caminho}")

finally:
    camera.release()
    cv2.destroyAllWindows()

print(
    f"\nCadastro encerrado para {aluno['nome']}. "
    f"Total de imagens nesta sessão: "
    f"{contador - len(existentes)}."
)
