# Fase 2 — Pipeline de Ingestão (Bronze Layer)

Este documento detalha o funcionamento do pipeline de ingestão de dados desenvolvido nesta fase. Nosso objetivo é buscar o dataset completo da Olist no Kaggle e carregá-lo de forma automatizada na nossa arquitetura de Data Lake (DBFS), estabelecendo a fundação da **Camada Bronze**.

---

## 🏗️ Como a Ingestão Funciona?

O pipeline foi construído no script `pipelines/download_data.py`. Ele realiza as seguintes operações orquestradas:

1. **Extração Automática (Kaggle API):** 
   O script se autentica na API do Kaggle e faz o download automático do pacote `olistbr/brazilian-ecommerce` (aprox. 45MB compactado) em uma pasta temporária `data/raw/`.

2. **Unzip & Preparação:**
   O pacote é descompactado revelando os 9 arquivos CSV cruciais para a análise (clientes, pedidos, avaliações, pagamentos, etc).

3. **Governança Ativa (AI Validation Layer Check):**
   Antes de permitir a subida para o Data Lake, o pipeline lê as regras estabelecidas em `ml_ops/validation_layer/rules.yaml`. Apenas os arquivos (tabelas) que estiverem mapeados na chave `allowed_tables` receberão permissão de upload. Se uma tabela desconhecida aparecer, ela é ignorada, prevenindo sujeira e alucinações futuras do modelo de IA.

4. **Carga na Nuvem (Databricks CLI):**
   Utilizando a Databricks CLI configurada na fase anterior, os arquivos autorizados são transferidos de forma nativa para o `dbfs:/olist/bronze/`.

5. **Sanitização Local:**
   A pasta temporária local é totalmente deletada para manter o ambiente de desenvolvimento livre de lixo residual (já que os dados agora estão seguros na nuvem).

---

## 🚀 Como Executar

Para simplificar a operação (uma boa prática em Data Engineering), criamos um atalho no `Makefile`. 

No diretório raiz do projeto (com a `venv` ativada), basta executar:

```bash
make ingest
```

### O que você verá no console:
Você verá uma série de logs mostrando cada etapa:
1. `📦 Baixando dataset...`
2. Mensagens do tipo `⬆️ [Governança: Aprovado] Enviando...` para cada tabela que foi autorizada pela *Validation Layer*.
3. Limpeza dos dados e conclusão da pipeline.

---

## 📊 Arquivos Disponibilizados na Bronze

Se a execução for concluída com sucesso, você terá no Databricks as seguintes tabelas em estado cru (formato CSV):

* `customers`
* `geolocation`
* `order_items`
* `order_payments`
* `order_reviews`
* `orders`
* `products`
* `sellers`
* `product_category_name_translation`

### 💡 Dica: Validando a Ingestão
Para ter certeza de que os arquivos chegaram com sucesso na nuvem sem precisar abrir o navegador, você pode listar os arquivos direto pelo seu terminal rodando:

```bash
databricks fs ls dbfs:/olist/bronze/
```

---

## Próxima Fase
Com a Bronze populada e a governança de IA já aplicando regras desde a origem, estamos prontos para plugar o Apache Spark e tratar esses dados na fase Silver.

→ Fase 3: Processamento e Limpeza (Silver Layer) *(Em breve)*
