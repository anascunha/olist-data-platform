# Descrição de colunas

{% docs customer_unique_id %}
Identificador único do cliente final no Olist. Um mesmo cliente recebe um `customer_id`
diferente a cada pedido; o `customer_unique_id` agrupa todos eles e é a chave usada para
ligar o marketplace ao CRM.
{% enddocs %}

{% docs order_status %}
Status do pedido no Olist: delivered, shipped, canceled, unavailable, invoiced, processing,
created ou approved. Pedidos `canceled` e `unavailable` não são considerados compras válidas
(var `invalid_order_statuses`).
{% enddocs %}

{% docs lifecycle_stage %}
Estágio do contato no funil do CRM:
- lead: contato captado, ainda não qualificado
- mql: lead qualificado pelo marketing
- opportunity: negociação em andamento
- customer: marcado como cliente pelo time comercial
- churned: cliente que deixou de comprar
- disqualified: lead descartado
{% enddocs %}

# Metadados

{% docs _ingestion_timestamp %}
Data e hora exata em que o registro foi ingerido no Data Lake.
{% enddocs %}

{% docs _source_schema %}
Fonte de origem do dado (olist ou crm).
{% enddocs %}

{% docs _source_table %}
Arquivo CSV de origem do dado.
{% enddocs %}

{% docs _source_database %}
Sistema de origem do dado (dataset Kaggle ou gerador do CRM).
{% enddocs %}

{% docs _storage_type %}
Tipo de armazenamento do dado no Data Lake.
{% enddocs %}
