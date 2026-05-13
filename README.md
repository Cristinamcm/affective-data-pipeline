# Affective Data Pipeline

O Pipeline de Dados Afetivos é um sistema protótipo concebido para suportar a recolha, preparação, estruturação e armazenamento de dados afetivos provenientes das redes sociais.

O sistema recebe dados de redes sociais em formato CSV ou JSON, armazena os dados brutos originais, aplica técnicas de pré-processamento e anonimização, extrai sinais afetivos relevantes e armazena os dados processados ​​num formato estruturado. Os dados resultantes podem então ser acedidos através de uma API REST, exportados para CSV/JSON ou visualizados num painel de controlo.

---

## 1. Contexto do Projeto

As plataformas de redes sociais geram grandes volumes de dados heterogéneos e ruidosos, incluindo conteúdo textual, emojis, hashtags, menções, URLs, reações e outros metadados. Estes elementos podem conter informação afetiva útil para a análise de sentimentos, deteção de emoções e sistemas de inteligência artificial subsequentes.

No entanto, antes de estes dados poderem ser utilizados eficazmente, devem ser recolhidos, limpos, anonimizados, normalizados, estruturados e armazenados de forma rastreável.

Este protótipo visa abordar este desafio implementando um pipeline modular de preparação de dados para dados afetivos de redes sociais.

---

## 2. Objectivo Principal

O principal objetivo deste sistema é transformar dados brutos das redes sociais em dados afetivos estruturados e reutilizáveis.

O sistema centra-se em:

- Importar conjuntos de dados de redes sociais;

- Preservar os dados brutos;

- Anonimizar elementos sensíveis;

- Limpar e normalizar conteúdo textual;

- Extrair emojis, hashtags, menções, URLs e palavras afetivas;

- Identificar sinais afetivos;

- Gerar indicadores afetivos;

- Armazenar dados processados;

- Expor resultados através de uma API;

- Disponibilizar um painel de controlo para demonstração e análise.

---

## 3. Principais Funcionalidades

O protótipo atual suporta:

- Importação de conjuntos de dados CSV/JSON;

- Armazenamento de dados brutos;

- Anonimização de texto;

- Normalização de texto;

- Extração de emojis;

- Extração de hashtags;

- Detecção de URLs e menções;

- Extração de sinais afetivos;

- Geração de perfis afetivos;

- Rastreio da execução do processamento;
- Cálculo de métricas de qualidade;

- Acesso à API REST;

- Exportação de dados;

- Visualização em painel.

---

## 4. Arquitetura do Sistema

O sistema segue uma arquitetura modular composta pelas seguintes camadas:

```text

Fonte de Dados
↓
Conectores
↓
Armazenamento de Dados Brutos
↓
Pipeline de Processamento
↓
Pré-processamento
↓
Extração de Sinais Afetivos
↓
Armazenamento Estruturado
↓
API / Painel / Exportação