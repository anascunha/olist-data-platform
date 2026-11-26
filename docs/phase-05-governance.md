# Fase 5 — Governança no Unity Catalog

Esta fase aplica controle de acesso e proteção de dados pessoais (PII) sobre as camadas já construídas, usando o **Unity Catalog** do Databricks Free Edition.

**Estado atual:** tudo abaixo foi **aplicado e testado pelo painel / SQL Editor** do Databricks. Os comandos estão documentados aqui, mas ainda **não são reaplicados automaticamente** pelo pipeline — levar isso para o código é o primeiro item do [roadmap](#-roadmap).

A proteção acontece em três peças complementares:

| Peça | O que faz | Onde |
|---|---|---|
| **GRANT** | Decide **quais tabelas** cada grupo vê | `producao.marts` |
| **Máscara de coluna** | Decide **quais valores** cada grupo vê dentro da tabela | `email` e `phone_e164` da `dim_crm_contact` |
| **Tag** | **Classifica** o dado (não bloqueia nada sozinha) | colunas pessoais da Bronze do CRM |

Antes de tudo isso, a ingestão já tem uma primeira barreira: só sobem para o Volume as tabelas da lista permitida em `ml_ops/validation_layer/rules.yaml` (ver [Fase 2](./phase-02-ingestion.md)).

---

## 👥 Grupos

| Grupo | Papel |
|---|---|
| `analistas` | Lê a Gold para responder às perguntas de negócio |
| `leitores_pii` | Vê e-mail e telefone completos (sem máscara) |

Os grupos precisam ser **de conta** (*account groups*). O metastore do Unity Catalog fica no nível da conta, então ele não reconhece grupos locais de workspace.

> ⚠️ `databricks groups create` cria um grupo **local do workspace** (`"resourceType": "WorkspaceGroup"`), e o `GRANT` falha com `Could not find principal`. Crie os grupos pela interface: **Settings → Identity and access → Groups → Add group**.

O acesso é sempre concedido a **grupos, nunca a pessoas**: quem entra no time é adicionado ao grupo e herda tudo; quem sai é removido, sem mexer em nenhum `GRANT`.

---

## 🔐 Privilégio mínimo: `analistas` só na Gold

Para ler uma tabela é preciso passar por três níveis:

```sql
GRANT USE CATALOG ON CATALOG producao      TO `analistas`;
GRANT USE SCHEMA  ON SCHEMA  producao.marts TO `analistas`;
GRANT SELECT      ON SCHEMA  producao.marts TO `analistas`;
```

* `USE CATALOG` só permite "entrar" no catálogo; não dá leitura.
* `SELECT` no **schema** vale para todas as tabelas atuais e futuras da `marts` (herança).
* `producao.staging` e `producao.trusted` ficam **sem acesso**: são camadas intermediárias, e a `tru_crm_contacts` contém dados pessoais.
* O catálogo `raw` (Bronze) também fica fora.

Conferência:

```sql
SHOW GRANTS ON CATALOG producao;
SHOW GRANTS ON SCHEMA producao.marts;
```

---

## 🎭 Máscaras de coluna (PII na Gold)

A `dim_crm_contact` ainda carrega `email` e `phone_e164`, então o `GRANT` sozinho não protege esses valores. Uma **column mask** é uma função SQL aplicada a cada leitura: o dado fica gravado inteiro e só quem está no grupo `leitores_pii` vê o valor real.

```sql
CREATE OR REPLACE FUNCTION producao.marts.mask_email(email STRING)
RETURNS STRING
RETURN CASE
  WHEN is_account_group_member('leitores_pii') THEN email
  ELSE regexp_replace(email, '^[^@]+', '***')            -- ***@dominio.com
END;

CREATE OR REPLACE FUNCTION producao.marts.mask_phone(phone_e164 STRING)
RETURNS STRING
RETURN CASE
  WHEN is_account_group_member('leitores_pii') THEN phone_e164
  ELSE concat(substr(phone_e164, 1, 5), '*********')      -- +5511********* (mantém país e DDD)
END;

ALTER TABLE producao.marts.dim_crm_contact ALTER COLUMN email      SET MASK producao.marts.mask_email;
ALTER TABLE producao.marts.dim_crm_contact ALTER COLUMN phone_e164 SET MASK producao.marts.mask_phone;
```

Decisões:
* O e-mail mantém o **domínio** e o telefone mantém **país e DDD**: o analista ainda consegue analisar por provedor ou região sem identificar a pessoa.
* Os asteriscos deixam claro que o valor foi **mascarado**, e não que veio quebrado da origem.
* A regra usa `is_account_group_member` (grupo de conta). `is_member` é a versão legada, para grupos locais.
* Alternativas descartadas: **view dinâmica** (um objeto a mais para manter e conceder) e **tabela cópia mascarada** (duplica dados e pode ficar desatualizada).

### Testes realizados

| Teste | Resultado |
|---|---|
| Usuária **admin**, fora de `leitores_pii` | `***@gmail.com` e `+5511*********` — a máscara vale até para admin |
| Mesma usuária, dentro de `leitores_pii` | e-mail e telefone completos |
| Job re-executado (o dbt recria a `dim_crm_contact`) | **a máscara continuou aplicada** — o `CREATE OR REPLACE TABLE` mantém a identidade da tabela no Unity Catalog |

O último teste refutou a hipótese inicial de que a máscara sumiria a cada `dbt build`. Ainda assim, ela não está no código: num ambiente novo, ou se o dbt precisar fazer `DROP` (por exemplo, ao trocar a materialização), a máscara não existiria.

---

## 🏷️ Tags de PII na Bronze do CRM

As colunas pessoais de `raw.source_crm.contacts` foram classificadas com a tag `pii`:

```sql
SET TAG ON COLUMN raw.source_crm.contacts.first_name         pii = name;
SET TAG ON COLUMN raw.source_crm.contacts.last_name          pii = name;
SET TAG ON COLUMN raw.source_crm.contacts.email              pii = email;
SET TAG ON COLUMN raw.source_crm.contacts.phone              pii = phone;
SET TAG ON COLUMN raw.source_crm.contacts.birth_date         pii = birth_date;
SET TAG ON COLUMN raw.source_crm.contacts.contact_id         pii = pseudonymous_id;
SET TAG ON COLUMN raw.source_crm.contacts.customer_unique_id pii = pseudonymous_id;
```

Conferência:

```sql
SELECT column_name, tag_name, tag_value
FROM raw.information_schema.column_tags
WHERE table_name = 'contacts';
```

* A tag **classifica**; quem protege são o `GRANT` (analistas não acessam `raw`) e as máscaras.
* `customer_unique_id` é **pseudonimizado**: não é nome nem contato, mas liga o contato a todo o histórico de compras — continua sendo dado pessoal.
* `pii` ainda é uma tag **livre** (não *governed*): qualquer valor é aceito.

---

## 🔗 Linhagem

O Unity Catalog captura a linhagem automaticamente (Catalog Explorer → tabela → **Lineage**), inclusive por coluna:

```
raw.source_crm.contacts → stg_crm__contacts → tru_crm_contacts → dim_crm_contact
```

**A tag não desce pela linhagem**: só a Bronze está classificada como PII. A linhagem é o que mostra para onde o `email` foi — e foi assim que a `dim_crm_contact` foi identificada como o ponto a mascarar na Gold.

---

## ⚠️ Limitações conhecidas

* **Aplicado pelo painel**: `GRANT`s, funções, máscaras e tags não estão no pipeline; um ambiente novo nasce sem eles.
* **Comentário da Bronze sobrescrito**: `pipelines/bronze.py` grava um `COMMENT ON TABLE` automático a cada ingestão, apagando qualquer comentário escrito à mão.
* **Quase-identificadores sem tag**: `city` e `state`, combinados com `birth_date`, podem reidentificar uma pessoa.
* **Job roda como usuária admin**: nada impede, hoje, uma execução com o target `prod` a partir de uma máquina pessoal.
* **Filtro da ingestão é fail-open**: se `allowed_tables` vier vazio, tudo passa (`pipelines/download_data.py`).

---

## 🧭 Roadmap

1. **Governança como código**
   * Máscaras declaradas no YAML do modelo dbt (`column_mask`, suportado nas versões recentes do `dbt-databricks`), para serem reaplicadas a cada build.
   * Funções de máscara, `GRANT`s e tags num script SQL idempotente versionado, executado pelo CD.
   * Ingestão preservando os comentários de governança da Bronze.
2. **Service principal no Job**: identidade técnica com acesso mínimo (lê `raw`, escreve `producao`) e **só ela** com escrita em `producao`.
3. **ABAC por tag**: transformar `pii` em *governed tag* (valores permitidos) e criar uma política que mascare toda coluna com, por exemplo, `pii = email` — tabelas novas já nascem protegidas.
4. **Ampliar a classificação**: tags nos quase-identificadores e nas colunas derivadas da Silver e da Gold.
5. **Filtro de ingestão fail-closed**: sem regra de governança, nada sobe.

---

## Próxima Fase
→ Fase 6: Interface analítica (Streamlit + agente NL2SQL) consumindo `producao.marts` *(planejada)*
