"""
Schemas de validação associados ao módulo de processamento.

Este módulo define a estrutura dos dados enviados pelo frontend ou por outro
cliente da API para iniciar uma execução de processamento.

Os schemas Pydantic permitem validar automaticamente os dados recebidos antes
de estes serem enviados para a camada de serviço.
"""

from pydantic import BaseModel, Field


class PreprocessingRequest(BaseModel):
    """
    Representa um pedido para executar o processamento de um conjunto de dados.

    O pedido contém:

    - um nome para identificar a configuração;
    - as operações que o utilizador pretende ativar ou desativar.

    Exemplo:

        {
            "configuration_name": "configuracao_personalizada",
            "config": {
                "lowercase": true,
                "normalize_spaces": true,
                "replace_urls": true,
                "anonymize_mentions": true,
                "remove_punctuation": false
            }
        }
    """

    configuration_name: str = Field(
        default="custom",
        min_length=1,
        max_length=100,
        description=(
            "Nome identificador da configuração "
            "de processamento."
        )
    )

    config: dict[str, bool] = Field(
        default_factory=dict,
        description=(
            "Operações selecionadas pelo utilizador, "
            "representadas por pares operação-estado."
        )
    )