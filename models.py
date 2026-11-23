
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Turma(Base):
    __tablename__ = "turmas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    ano_letivo = Column(Integer, nullable=False)

    alunos = relationship("Aluno", back_populates="turma")


class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    matricula = Column(String(30), unique=True, nullable=False, index=True)
    ativo = Column(Boolean, default=True, nullable=False)

    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=True)
    turma = relationship("Turma", back_populates="alunos")
from sqlalchemy import Date, Time, UniqueConstraint
class Presenca(Base):
    __tablename__ = "presencas"

    __table_args__ = (
        UniqueConstraint(
            "aluno_id",
            "data",
            name="uq_presenca_aluno_data"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    aluno_id = Column(
        Integer,
        ForeignKey("alunos.id"),
        nullable=False,
        index=True
    )

    turma_id = Column(
        Integer,
        ForeignKey("turmas.id"),
        nullable=True
    )

    data = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=False)
    status = Column(String(20), nullable=False, default="Presente")