"""
Schemas de validação associados ao módulo de pré-processamento.

Este módulo define a estrutura dos dados que devem ser enviados pelo frontend
ou por outro cliente da API para iniciar uma execução de pré-processamento.

Os schemas Pydantic permitem validar automaticamente os dados recebidos antes
de estes serem enviados para a camada de serviço.
"""

from pydantic import BaseModel, Field


class PreprocessingRequest(BaseModel):
    """
    Representa um pedido para executar o pré-processamento de um dataset.

    O pedido contém o nome da configuração e um dicionário com as operações
    de pré-processamento que o utilizador pretende ativar ou desativar.

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

    # Nome atribuído à configuração de pré-processamento.
    #
    # Quando o frontend não fornece um nome, é utilizado "custom", indicando
    # que se trata de uma configuração personalizada pelo utilizador.
    configuration_name: str = Field(
        default="custom",
        description="Nome identificador da configuração de pré-processamento."
    )

    # Conjunto de operações de pré-processamento e respetivo estado.
    #
    # Cada chave corresponde a uma operação suportada pelo pipeline e cada
    # valor booleano indica se essa operação deverá ser aplicada.
    config: dict[str, bool] = Field(
        description=(
            "Operações de pré-processamento selecionadas pelo utilizador, "
            "representadas por pares operação-estado."
        )
    )