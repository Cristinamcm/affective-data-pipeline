"""
Schemas associados ao módulo de enriquecimento afetivo.
"""

from pydantic import BaseModel, Field


class AffectiveEnrichmentRequest(BaseModel):
    """
    Representa um pedido de enriquecimento afetivo.

    O idioma pode ser indicado explicitamente. Quando não é fornecido,
    o serviço utiliza o idioma registado no conjunto de dados.
    """

    language: str | None = Field(
        default=None,
        max_length=20,
        description=(
            "Código opcional do idioma utilizado na identificação "
            "de termos afetivos, por exemplo 'en' ou 'pt'."
        )
    )