# Fase 3 — CRM Fictício ligado ao Olist

O dataset do Olist mostra **o que** os clientes compram, mas não **quem** o time comercial e de marketing acompanha. Para responder perguntas como *"quais contatos do CRM compram no marketplace, quanto e com que frequência?"*, esta fase gera um **CRM genérico com dados fictícios** e o liga aos clientes reais do Olist pelo `customer_unique_id`.

> Todos os nomes, e-mails, telefones e datas de nascimento são gerados com [Faker](https://faker.readthedocs.io/) (`pt_BR`). Do Olist são reaproveitados apenas `customer_unique_id`, cidade e estado, que já são públicos e anonimizados no dataset original.

---

## 🧩 Modelo do CRM

```text
owners (12) ──┐
              ├──< contacts (20.000 + 400 duplicados) >──── customer_unique_id ──> Olist
campaigns (32)┘          │
                         └──< activities (~32 mil)
```

| Tabela Bronze | Grão | Colunas principais |
|---|---|---|
| `raw.source_crm.owners` | vendedor/analista | `owner_id`, `owner_name`, `team`, `region`, `hired_at`, `is_active` |
| `raw.source_crm.campaigns` | campanha de marketing | `campaign_id`, `campaign_name`, `channel`, `start_date`, `end_date`, `budget_brl` |
| `raw.source_crm.contacts` | contato (com duplicidades) | `contact_id`, `customer_unique_id`, nome, `email`, `phone`, `city`, `state`, `lifecycle_stage`, `lead_source`, `campaign_id`, `owner_id`, `marketing_opt_in`, `created_at`, `updated_at` |
| `raw.source_crm.activities` | interação | `activity_id`, `contact_id`, `owner_id`, `activity_type`, `direction`, `activity_at`, `outcome`, `duration_minutes` |

---

## 🎲 Regras de geração

| Regra | Valor padrão | Por quê |
|---|---|---|
| Contatos | 20.000 | Volume suficiente para análises por segmento |
| Ligados ao Olist (`--match-rate`) | 75% | Os outros 25% são leads que **nunca compraram**, o grupo de controle da pergunta de negócio |
| Recompradores entre os ligados | 8% (vs. ~3% no Olist) | CRMs concentram clientes engajados, e isso dá massa para a análise de frequência |
| Criação do contato | 75% antes da 1ª compra (até 240 dias), 25% depois (pós-venda) | Permite medir compras **antes vs. depois** de entrar no CRM |
| Campanha de origem | 70% dos contatos, campanha iniciada até 90 dias antes da criação | Atribuição coerente com o tempo |
| Campanhas | 1 por mês (jan/2016 a ago/2018), tema sazonal (Black Friday em novembro, Natal em dezembro…) | Realismo |
| `lifecycle_stage` ligados | customer 70%, opportunity 12%, lead 12%, churned 6% | CRM **desatualizado**: clientes que compram mas ainda aparecem como lead |
| `lifecycle_stage` não ligados | lead 55%, mql 20%, opportunity 15%, disqualified 10% | Funil típico |

### Problemas de qualidade propositais (tratados na Silver)

* **2% de contatos duplicados:** mesmo `contact_id`, versão mais antiga (`updated_at` menor, estágio `lead`). A trusted mantém a versão mais recente.
* **E-mails sujos:** espaços, maiúsculas e e-mails vazios.
* **Telefones em 3 formatos:** `(11) 91234-5678`, `+5511912345678` e `11912345678`.

A geração é **determinística** (`--seed 42` e `faker==40.44.0` fixados): rodar de novo produz exatamente os mesmos arquivos.

---

## 🚀 Como Executar

Pré-requisito: Fase 2 executada. O gerador lê `data/landing/olist/olist_customers_dataset.csv` e `olist_orders_dataset.csv`.

```bash
make crm
```

Equivale a `python -m pipelines.generate_crm`. Parâmetros disponíveis: `--contacts`, `--match-rate`, `--seed`, `--olist-dir`, `--output-dir`, `--skip-upload`.

Saída esperada:

```text
🛒 96,096 clientes únicos com pedidos no Olist
📝 data/landing/crm/crm_owners.csv (12 linhas)
📝 data/landing/crm/crm_campaigns.csv (32 linhas)
📝 data/landing/crm/crm_contacts.csv (20,400 linhas)
📝 data/landing/crm/crm_activities.csv (32,304 linhas)

👥 Contatos únicos: 20,000 | duplicados: 400
🔗 Ligados ao Olist (customer_unique_id): 15,000 (75%)
```

Os CSVs são enviados para `/Volumes/raw/source_crm/landing/`. Em seguida, rode o notebook `databricks/ingestao_bronze.py` com `source = crm` para criar as tabelas `raw.source_crm.*`.

---

## Próxima Fase
→ [Fase 4 — Transformação com dbt (Silver e Gold)](./phase-04-dbt.md)
