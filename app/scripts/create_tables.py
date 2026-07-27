"""
Script de criação das tabelas da base de dados.

Este módulo utiliza os modelos ORM registados no SQLAlchemy para criar,
na base de dados configurada, todas as tabelas necessárias ao funcionamento
do sistema.

O script é especialmente útil durante a configuração inicial do protótipo
ou em ambientes de desenvolvimento.
"""

from app.database import Base, engine

# A importação do módulo de modelos garante que todas as classes ORM são
# registadas no metadata do SQLAlchemy antes da criação das tabelas.
from app.models import models


def create_tables():
    """
    Cria na base de dados todas as tabelas registadas no metadata do SQLAlchemy.

    Apenas são criadas as tabelas que ainda não existem. Este método não altera
    automaticamente a estrutura de tabelas já existentes.
    """

    # Percorre os modelos que herdam de Base e cria as respetivas tabelas
    # através do engine configurado em app.database.
    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully.")


# Executa a criação das tabelas apenas quando este ficheiro é iniciado
# diretamente, evitando a execução automática quando é importado por outro
# módulo da aplicação.
if __name__ == "__main__":
    create_tables()