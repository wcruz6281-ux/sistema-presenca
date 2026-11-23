"""Cadastro e treinamento facial pelo navegador.

O navegador envia fotos da webcam; o servidor detecta o rosto com o OpenCV
(mesmo detector e mesmo recorte do cadastrar_rosto.py) e salva em
rostos_alunos/aluno_<ID>/rosto_NNN.png, que é a pasta lida pelo
treinar_rosto.py e usada pelo reconhecer_rosto.py.
"""

import base64
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import SessionLocal

try:
    import cv2
    import numpy as np
except ImportError:  # o restante da API continua funcionando sem OpenCV
    cv2 = None
    np = None

router = APIRouter(tags=["Reconhecimento facial"])

# Caminhos relativos à pasta onde o uvicorn é iniciado,
# a mesma usada pelos scripts cadastrar/treinar/reconhecer.
PASTA_BASE = Path("rostos_alunos")
ARQUIVO_MODELO = Path("modelo_rosto.yml")
LIMITE_IMAGENS = 30
MAX_CARACTERES = 3_000_000

_classificador = None


def _banco():
    banco = SessionLocal()
    try:
        yield banco
    finally:
        banco.close()


def _exigir_opencv():
    if cv2 is None:
        raise HTTPException(
            status_code=500,
            detail="OpenCV não instalado. Rode: pip install opencv-contrib-python"
        )


def _detector():
    global _classificador

    if _classificador is None:
        _classificador = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

    return _classificador


def _pasta(aluno_id: int) -> Path:
    return PASTA_BASE / f"aluno_{aluno_id}"


def _arquivos(aluno_id: int):
    pasta = _pasta(aluno_id)
    return sorted(pasta.glob("rosto_*.png")) if pasta.exists() else []


class ImagemRosto(BaseModel):
    imagem: str  # JPEG/PNG em base64 (aceita o prefixo data:image/...)


@router.get("/rostos/status")
def status_rostos():
    """Quantas imagens cada aluno já tem."""
    resultado = []

    if PASTA_BASE.exists():
        for pasta in sorted(PASTA_BASE.glob("aluno_*")):
            try:
                aluno_id = int(pasta.name.replace("aluno_", ""))
            except ValueError:
                continue

            resultado.append({
                "aluno_id": aluno_id,
                "imagens": len(list(pasta.glob("rosto_*.png")))
            })

    return resultado


@router.post("/alunos/{aluno_id}/rosto/imagem")
def salvar_imagem_rosto(
    aluno_id: int,
    dados: ImagemRosto,
    banco: Session = Depends(_banco)
):
    _exigir_opencv()

    aluno = banco.query(models.Aluno).filter_by(id=aluno_id).first()

    if aluno is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")

    if not aluno.ativo:
        raise HTTPException(status_code=400, detail="Aluno inativo.")

    existentes = _arquivos(aluno_id)

    if len(existentes) >= LIMITE_IMAGENS:
        return {"salvo": False, "motivo": "limite", "total": len(existentes)}

    texto = dados.imagem

    if "," in texto:
        texto = texto.split(",", 1)[1]

    if len(texto) > MAX_CARACTERES:
        raise HTTPException(status_code=400, detail="Imagem muito grande.")

    try:
        bruto = base64.b64decode(texto, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Imagem inválida.")

    quadro = cv2.imdecode(np.frombuffer(bruto, np.uint8), cv2.IMREAD_COLOR)

    if quadro is None:
        raise HTTPException(status_code=400, detail="Imagem inválida.")

    cinza = cv2.cvtColor(quadro, cv2.COLOR_BGR2GRAY)

    rostos = _detector().detectMultiScale(
        cinza,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(rostos) == 0:
        return {
            "salvo": False,
            "motivo": "nenhum_rosto",
            "total": len(existentes)
        }

    if len(rostos) > 1:
        # Evita cadastrar o rosto de outra pessoa por engano.
        return {
            "salvo": False,
            "motivo": "varios_rostos",
            "total": len(existentes)
        }

    x, y, w, h = rostos[0]
    rosto = cv2.resize(cinza[y:y + h, x:x + w], (200, 200))

    pasta = _pasta(aluno_id)
    pasta.mkdir(parents=True, exist_ok=True)

    numeros = [int(a.stem.split("_")[1]) for a in existentes]
    proximo = (max(numeros) if numeros else 0) + 1
    caminho = pasta / f"rosto_{proximo:03d}.png"

    if not cv2.imwrite(str(caminho), rosto):
        raise HTTPException(
            status_code=500,
            detail="Não foi possível salvar a imagem."
        )

    return {"salvo": True, "total": len(existentes) + 1}


@router.post("/rostos/treinar")
def treinar_modelo():
    """Mesma lógica do treinar_rosto.py."""
    _exigir_opencv()

    if not hasattr(cv2, "face"):
        raise HTTPException(
            status_code=500,
            detail=(
                "Módulo cv2.face ausente. Instale: "
                "pip install opencv-contrib-python"
            )
        )

    imagens = []
    identificacoes = []

    if PASTA_BASE.exists():
        for pasta in sorted(PASTA_BASE.glob("aluno_*")):
            try:
                aluno_id = int(pasta.name.replace("aluno_", ""))
            except ValueError:
                continue

            for arquivo in pasta.glob("rosto_*.png"):
                imagem = cv2.imread(str(arquivo), cv2.IMREAD_GRAYSCALE)

                if imagem is None:
                    continue

                imagens.append(cv2.resize(imagem, (200, 200)))
                identificacoes.append(aluno_id)

    if len(imagens) < 5:
        raise HTTPException(
            status_code=400,
            detail="Poucas imagens para treinar. Cadastre pelo menos 5."
        )

    reconhecedor = cv2.face.LBPHFaceRecognizer_create()
    reconhecedor.train(imagens, np.array(identificacoes, dtype=np.int32))
    reconhecedor.write(str(ARQUIVO_MODELO))

    return {
        "mensagem": (
            f"Modelo treinado com {len(imagens)} imagens de "
            f"{len(set(identificacoes))} aluno(s)."
        ),
        "imagens": len(imagens),
        "alunos": len(set(identificacoes))
    }


@router.delete("/alunos/{aluno_id}/rosto")
def remover_rosto(aluno_id: int):
    """Apaga as imagens do aluno (ex.: pedido de exclusão dos dados)."""
    pasta = _pasta(aluno_id)

    if not pasta.exists():
        raise HTTPException(status_code=404, detail="Rosto não cadastrado.")

    shutil.rmtree(pasta)

    return {
        "mensagem": "Imagens removidas. Treine o modelo novamente."
    }