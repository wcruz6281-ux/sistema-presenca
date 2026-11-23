
import cv2
import numpy as np
from pathlib import Path

PASTA_BASE = Path("rostos_alunos")
ARQUIVO_MODELO = Path("modelo_rosto.yml")

imagens = []
identificacoes = []

if not PASTA_BASE.exists():
    print("Pasta rostos_alunos não encontrada.")
    raise SystemExit

# Cada pasta aluno_ID corresponde ao ID do banco de dados.
for pasta_aluno in sorted(PASTA_BASE.glob("aluno_*")):
    try:
        aluno_id = int(pasta_aluno.name.replace("aluno_", ""))
    except ValueError:
        continue

    arquivos = list(pasta_aluno.glob("rosto_*.png"))

    if not arquivos:
        continue

    for arquivo in arquivos:
        imagem = cv2.imread(str(arquivo), cv2.IMREAD_GRAYSCALE)

        if imagem is None:
            print(f"Imagem ignorada: {arquivo}")
            continue

        imagem = cv2.resize(imagem, (200, 200))
        imagens.append(imagem)
        identificacoes.append(aluno_id)

    print(f"Aluno ID {aluno_id}: {len(arquivos)} arquivo(s) encontrado(s).")

if len(imagens) < 5:
    print("Poucas imagens para treinar. Cadastre pelo menos 5 imagens.")
    raise SystemExit

if len(set(identificacoes)) < 1:
    print("Nenhum aluno com imagens válidas foi encontrado.")
    raise SystemExit

reconhecedor = cv2.face.LBPHFaceRecognizer_create()
reconhecedor.train(imagens, np.array(identificacoes, dtype=np.int32))
reconhecedor.write(str(ARQUIVO_MODELO))

print("\nTreinamento concluído!")
print(f"Imagens utilizadas: {len(imagens)}")
print(f"Alunos treinados: {len(set(identificacoes))}")
print(f"Modelo salvo em: {ARQUIVO_MODELO}")
