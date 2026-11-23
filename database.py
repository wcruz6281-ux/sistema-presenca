
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Arquivo onde os dados do sistema serão armazenados
DATABASE_URL = "sqlite:///./presenca.db"

# Cria a conexão com o banco de dados
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Cria as sessões usadas para consultar e salvar dados
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Classe-base para criar as tabelas do banco
Base = declarative_base()


def criar_banco():
    """Cria as tabelas definidas no sistema."""
    Base.metadata.create_all(bind=engine)
