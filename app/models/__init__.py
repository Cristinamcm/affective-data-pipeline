"""
Disponibiliza os modelos ORM definidos no pacote app.models.

A centralização das importações neste ficheiro permite importar os modelos
diretamente a partir do pacote, sem ser necessário indicar o módulo interno
models.py em cada utilização.
"""

from app.models.models import (
    Dataset,
    Post,
    ProcessingRun,
    ProcessedPost
)


# Define explicitamente os elementos públicos disponibilizados por este pacote.
#
# Com esta definição, instruções como `from app.models import *` apenas importam
# os modelos listados abaixo.
__all__ = [
    "Dataset",
    "Post",
    "ProcessingRun",
    "ProcessedPost"
]