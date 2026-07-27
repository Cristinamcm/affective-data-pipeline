"""
Serviço responsável por coordenar o pré-processamento de datasets.

Este módulo implementa a lógica aplicacional necessária para:

1. validar a existência do dataset;
2. normalizar a configuração escolhida pelo utilizador;
3. obter as publicações originais;
4. criar o registo da execução de pré-processamento;
5. identificar publicações duplicadas;
6. aplicar o pipeline a cada publicação;
7. guardar os resultados e as métricas;
8. finalizar a execução com sucesso ou erro.

A camada de serviço coordena os diferentes componentes do sistema, mantendo
separadas a lógica de pré-processamento e a lógica de acesso à base de dados.
"""

from sqlalchemy.orm import Session

from app.preprocessing.preprocessing_pipeline import preprocess_text
from app.preprocessing.presets import normalize_config
from app.repositories.dataset_repository import get_dataset_by_id
from app.repositories.preprocessing_repository import (
    create_processing_run,
    finish_processing_run,
    get_all_posts_by_dataset,
    save_processed_post
)


def preprocess_dataset(
    db: Session,
    dataset_id: int,
    configuration_name: str,
    config: dict[str, bool]
):
    dataset = get_dataset_by_id(
        db=db,
        dataset_id=dataset_id
    )

    if dataset is None:
        raise ValueError("Dataset not found")

    normalized_config = normalize_config(config)

    posts = get_all_posts_by_dataset(
        db=db,
        dataset_id=dataset_id
    )

    run = create_processing_run(
        db=db,
        dataset_id=dataset_id,
        configuration_name=configuration_name,
        configuration_json=normalized_config,
        total_posts=len(posts)
    )

    # Conjunto utilizado para guardar versões normalizadas dos textos já
    # encontrados. A utilização de um set permite verificar duplicados de forma
    # eficiente durante a iteração.
    seen_texts = set()

    # Contadores agregados da execução.
    duplicate_posts = 0
    empty_after_processing = 0
    processed_posts_count = 0

    try:
        # Processa sequencialmente cada publicação original do dataset.
        for post in posts:

            # Produz uma versão mínima normalizada do texto para deteção de
            # duplicados, ignorando diferenças de maiúsculas, minúsculas e
            # espaços existentes no início ou no fim.
            original_normalized = post.original_text.strip().lower()

            # Por omissão, a publicação atual não é considerada duplicada.
            is_duplicate = False

            # Quando a normalização de espaços está ativa, sequências de
            # múltiplos espaços, tabulações ou mudanças de linha são reduzidas
            # a um único espaço antes da comparação entre publicações.
            if normalized_config.get("normalize_spaces"):
                original_normalized = " ".join(original_normalized.split())

            # Verifica se já foi encontrada uma publicação com o mesmo texto
            # normalizado durante a execução atual.
            if original_normalized in seen_texts:
                is_duplicate = True
                duplicate_posts += 1
            else:
                # Regista o texto como já encontrado para permitir a deteção de
                # ocorrências repetidas nas publicações seguintes.
                seen_texts.add(original_normalized)

            # Aplica ao texto original as operações de pré-processamento
            # selecionadas pelo utilizador.
            #
            # O resultado deverá incluir o texto processado, elementos extraídos
            # e métricas como URLs, menções, hashtags, emojis e comprimentos.
            processed_data = preprocess_text(
                text=post.original_text,
                config=normalized_config
            )

            # Atualiza o contador quando todas as operações aplicadas resultam
            # num texto vazio.
            if processed_data["is_empty_after_processing"]:
                empty_after_processing += 1

            # Guarda o resultado individual, associando-o à publicação original
            # e à execução de processamento atual.
            save_processed_post(
                db=db,
                post=post,
                run=run,
                processed_data=processed_data,
                is_duplicate=is_duplicate
            )

            # Incrementa o número de publicações concluídas com sucesso.
            processed_posts_count += 1

        # Atualiza o registo da execução após todas as publicações terem sido
        # processadas com sucesso.
        finish_processing_run(
            db=db,
            run=run,
            processed_posts_count=processed_posts_count,
            duplicate_posts=duplicate_posts,
            empty_after_processing=empty_after_processing,
            status="finished"
        )

        # Devolve à camada da API um resumo da execução concluída.
        return {
            "processing_run_id": run.id,
            "dataset_id": dataset_id,
            "configuration_name": configuration_name,
            "total_posts": len(posts),
            "processed_posts": processed_posts_count,
            "duplicate_posts": duplicate_posts,
            "empty_after_processing": empty_after_processing,
            "status": "finished"
        }

    except Exception as error:
        # Regista a execução como falhada, preservando as métricas acumuladas
        # até ao momento e a mensagem do erro ocorrido.
        finish_processing_run(
            db=db,
            run=run,
            processed_posts_count=processed_posts_count,
            duplicate_posts=duplicate_posts,
            empty_after_processing=empty_after_processing,
            status="failed",
            error_message=str(error)
        )

        # Propaga a exceção original para que a camada da API possa devolver
        # uma resposta de erro adequada.
        raise