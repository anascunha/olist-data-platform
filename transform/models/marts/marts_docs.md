{% docs agg_crm_contact_purchases %}
Tabela principal da Gold: responde **quais contatos do CRM compram no marketplace, quanto
e com que frequência**.

Um registro por contato do CRM, inclusive os que nunca compraram (`buyer_segment = never_bought`).
Apenas pedidos válidos entram nas métricas (status fora de `invalid_order_statuses`).

Métricas de frequência:
- `total_orders`: pedidos válidos
- `avg_days_between_orders`: (último pedido - primeiro pedido) / (pedidos - 1), só para recompradores
- `recency_days`: dias entre o último pedido do contato e o último pedido do dataset
  (o Olist é um snapshot histórico de set/2016 a out/2018, então `current_date` não faz sentido)

Métricas de relacionamento com o CRM:
- `days_from_crm_entry_to_first_order`: negativo quando o cliente já comprava antes de entrar no CRM
- `orders_after_crm_entry` / `revenue_after_crm_entry`: compras feitas depois da criação do contato
- `is_stage_outdated`: compra no marketplace, mas o CRM ainda o trata como lead/mql/opportunity
{% enddocs %}

{% docs agg_crm_purchases_by_segment %}
Consolidação da `agg_crm_contact_purchases` por dimensão do CRM, em formato longo
(`dimension_name` / `dimension_value`). Dimensões: overall, lead_source, lifecycle_stage,
owner_team, buyer_segment e contact_state.

Use `where dimension_name = 'lead_source'` para comparar canais, por exemplo.
{% enddocs %}
