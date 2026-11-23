from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

import models
from sqlalchemy import func
from database import SessionLocal, criar_banco
from rosto_api import router as rosto_router

# Cria somente as tabelas que ainda não existem.
# Não apaga nem recria as tabelas existentes.
criar_banco()

app = FastAPI(title="Sistema de Presença Escolar")
app.include_router(rosto_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


class RegistroPresenca(BaseModel):
    aluno_id: int


def obter_banco():
    banco = SessionLocal()
    try:
        yield banco
    finally:
        banco.close()


@app.get("/")
def inicio():
    return FileResponse("static/index.html")


@app.post("/turmas")
def cadastrar_turma(
    nome: str,
    ano_letivo: int,
    banco: Session = Depends(obter_banco)
):
    turma = models.Turma(
        nome=nome,
        ano_letivo=ano_letivo
    )

    banco.add(turma)
    banco.commit()
    banco.refresh(turma)

    return {
        "mensagem": "Turma cadastrada com sucesso!",
        "id": turma.id,
        "nome": turma.nome,
        "ano_letivo": turma.ano_letivo
    }


@app.get("/turmas")
def listar_turmas(banco: Session = Depends(obter_banco)):
    turmas = banco.query(models.Turma).all()

    return [
        {
            "id": turma.id,
            "nome": turma.nome,
            "ano_letivo": turma.ano_letivo
        }
        for turma in turmas
    ]


@app.post("/alunos")
def cadastrar_aluno(
    nome: str,
    matricula: str,
    turma_id: int | None = None,
    banco: Session = Depends(obter_banco)
):
    existente = banco.query(models.Aluno).filter_by(
        matricula=matricula
    ).first()

    if existente:
        raise HTTPException(
            status_code=400,
            detail="Já existe um aluno com essa matrícula."
        )

    if turma_id is not None:
        turma = banco.query(models.Turma).filter_by(
            id=turma_id
        ).first()

        if turma is None:
            raise HTTPException(
                status_code=404,
                detail="Turma não encontrada."
            )

    aluno = models.Aluno(
        nome=nome,
        matricula=matricula,
        turma_id=turma_id
    )

    banco.add(aluno)
    banco.commit()
    banco.refresh(aluno)

    return {
        "mensagem": "Aluno cadastrado com sucesso!",
        "id": aluno.id,
        "nome": aluno.nome,
        "matricula": aluno.matricula,
        "turma_id": aluno.turma_id
    }


@app.get("/alunos")
def listar_alunos(banco: Session = Depends(obter_banco)):
    alunos = banco.query(models.Aluno).all()

    return [
        {
            "id": aluno.id,
            "nome": aluno.nome,
            "matricula": aluno.matricula,
            "ativo": aluno.ativo,
            "turma_id": aluno.turma_id
        }
        for aluno in alunos
    ]


@app.post("/presencas/registrar")
def registrar_presenca(
    dados: RegistroPresenca,
    banco: Session = Depends(obter_banco)
):
    aluno = banco.query(models.Aluno).filter_by(
        id=dados.aluno_id
    ).first()

    if aluno is None:
        raise HTTPException(
            status_code=404,
            detail="Aluno não encontrado."
        )

    if not aluno.ativo:
        raise HTTPException(
            status_code=400,
            detail="Aluno inativo. Presença não registrada."
        )

    agora = datetime.now()
    data_atual = agora.date()

    existente = banco.query(models.Presenca).filter_by(
        aluno_id=aluno.id,
        data=data_atual
    ).first()

    if existente:
        return {
            "mensagem": "Presença já registrada hoje.",
            "aluno": aluno.nome,
            "data": existente.data.isoformat(),
            "hora": existente.hora.strftime("%H:%M:%S"),
            "duplicada": True
        }

    presenca = models.Presenca(
        aluno_id=aluno.id,
        turma_id=aluno.turma_id,
        data=data_atual,
        hora=agora.time().replace(microsecond=0),
        status="Presente"
    )

    try:
        banco.add(presenca)
        banco.commit()
        banco.refresh(presenca)

        return {
            "mensagem": "Presença registrada com sucesso!",
            "aluno": aluno.nome,
            "aluno_id": aluno.id,
            "data": presenca.data.isoformat(),
            "hora": presenca.hora.strftime("%H:%M:%S"),
            "duplicada": False
        }

    except IntegrityError:
        banco.rollback()

        existente = banco.query(models.Presenca).filter_by(
            aluno_id=aluno.id,
            data=data_atual
        ).first()

        if existente:
            return {
                "mensagem": "Presença já registrada hoje.",
                "aluno": aluno.nome,
                "data": existente.data.isoformat(),
                "hora": existente.hora.strftime("%H:%M:%S"),
                "duplicada": True
            }

        raise HTTPException(
            status_code=409,
            detail="Não foi possível registrar a presença."
        )

@app.get("/dashboard/resumo")
def resumo_dashboard(banco: Session = Depends(obter_banco)):
    hoje = datetime.now().date()

    # Quantidade total de alunos
    total_alunos = banco.query(models.Aluno).count()

    # Quantidade de alunos ativos
    alunos_ativos = banco.query(models.Aluno).filter(
        models.Aluno.ativo == True
    ).count()

    # Quantidade de turmas
    total_turmas = banco.query(models.Turma).count()

    # Presenças de alunos ativos registradas hoje
    presencas_hoje = banco.query(models.Presenca).join(
        models.Aluno,
        models.Presenca.aluno_id == models.Aluno.id
    ).filter(
        models.Presenca.data == hoje,
        models.Aluno.ativo == True
    ).count()

    # Alunos ativos sem registro de presença hoje
    sem_registro = max(alunos_ativos - presencas_hoje, 0)

    # Cinco registros mais recentes
    registros = banco.query(
        models.Presenca,
        models.Aluno
    ).join(
        models.Aluno,
        models.Presenca.aluno_id == models.Aluno.id
    ).order_by(
        models.Presenca.data.desc(),
        models.Presenca.hora.desc()
    ).limit(5).all()

    recentes = []

    for presenca, aluno in registros:
        recentes.append({
            "aluno": aluno.nome,
            "matricula": aluno.matricula,
            "data": presenca.data.isoformat(),
            "hora": presenca.hora.strftime("%H:%M:%S"),
            "status": presenca.status
        })

    return {
        "total_alunos": total_alunos,
        "alunos_ativos": alunos_ativos,
        "total_turmas": total_turmas,
        "presencas_hoje": presencas_hoje,
        "sem_registro_hoje": sem_registro,
        "registros_recentes": recentes
    }