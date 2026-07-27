"""
Configuração da ligação à base de dados.

Este módulo é responsável por:

- carregar as variáveis de ambiente;
- obter o endereço de ligação à base de dados;
- criar o engine do SQLAlchemy;
- configurar a fábrica de sessões;
- disponibilizar a classe base dos modelos ORM;
- fornecer sessões de base de dados aos endpoints e serviços da aplicação.
"""


import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Carrega para o ambiente da aplicação as variáveis definidas no ficheiro .env.
#
# Esta abordagem permite manter configurações sensíveis ou dependentes do
# ambiente, como o endereço da base de dados, separadas do código-fonte.
load_dotenv()


# Obtém o endereço de ligação à base de dados através da variável de ambiente
# DATABASE_URL.
#
# Quando a variável não está definida, é utilizada uma base de dados SQLite
# local, armazenada no ficheiro affective_data.db.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./affective_data.db"
)


# Argumentos adicionais utilizados na criação da ligação à base de dados.
#
# Por omissão, não são necessários argumentos adicionais.
connect_args = {}


# O SQLite restringe, por omissão, a utilização de uma ligação à thread onde
# esta foi criada. Como o FastAPI pode processar pedidos em threads diferentes,
# esta opção permite que a mesma ligação seja utilizada nesse contexto.
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Cria o engine do SQLAlchemy, responsável por gerir as ligações entre a
# aplicação e a base de dados.
engine = create_engine(
    DATABASE_URL,
    # Verifica se uma ligação ainda se encontra válida antes de a disponibilizar.
    pool_pre_ping=True,
    # Aplica argumentos específicos do sistema de base de dados utilizado.
    connect_args=connect_args
)

# Cria uma fábrica de sessões SQLAlchemy.
#
# Cada sessão representa uma unidade de trabalho com a base de dados, através
# da qual podem ser realizadas consultas, inserções, atualizações e remoções.
SessionLocal = sessionmaker(
        # As transações não são confirmadas automaticamente.
    # O commit deve ser realizado explicitamente nos repositórios ou serviços.
    autocommit=False,
    # Evita que alterações pendentes sejam automaticamente enviadas para a
    # base de dados antes de determinadas consultas.
    autoflush=False,
    # Associa as sessões ao engine configurado anteriormente.
    bind=engine
)

# Classe base utilizada por todos os modelos ORM da aplicação.
#
# As classes que representam tabelas da base de dados devem herdar de Base.
Base = declarative_base()


def get_db():
    """
    Disponibiliza uma sessão de base de dados durante o processamento de um pedido.

    Esta função é utilizada como dependência do FastAPI. A sessão é criada antes
    da execução do endpoint e encerrada automaticamente no final, mesmo quando
    ocorre uma exceção.

    Yields:
        Session: Sessão SQLAlchemy associada à base de dados.
    """

    # Cria uma nova sessão para o pedido atual.    
    db = SessionLocal()

    try:
        # Disponibiliza a sessão ao endpoint, serviço ou repositório que declarou
        # esta função como dependência.        
        yield db
    finally:
        # Garante a libertação dos recursos da ligação à base de dados.
        db.close()