# Fase 1 — Infraestrutura e Configuração do Ambiente

Este documento guia a configuração completa da infraestrutura necessária para rodar a plataforma localmente e provisionar os recursos na Azure.

---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

| Ferramenta | Versão mínima | Download |
|---|---|---|
| Docker Desktop | 24+ | https://www.docker.com/products/docker-desktop |
| Terraform CLI | 1.5+ | https://developer.hashicorp.com/terraform/install |
| Azure CLI | 2.50+ | https://learn.microsoft.com/pt-br/cli/azure/install-azure-cli |
| Git | qualquer | https://git-scm.com |

---

## 1. Clonar o repositório

```bash
git clone https://github.com/<seu-usuario>/olist-data-platform.git
cd olist-data-platform
```

---

## 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha as credenciais nas próximas etapas:

```bash
cp .env.example .env
```

O arquivo `.env` **nunca deve ser commitado**. Ele já está no `.gitignore`.

---

## 3. Credenciais do Kaggle

O dataset da Olist vem da plataforma Kaggle. É necessário gerar um token de API:

1. Acesse [kaggle.com](https://www.kaggle.com) e faça login
2. Vá em **Settings → API → Create New Token**
3. Um arquivo `kaggle.json` será baixado com o seguinte conteúdo:
   ```json
   {"username": "seu_usuario", "key": "sua_chave"}
   ```
4. Preencha no `.env`:
   ```bash
   KAGGLE_USERNAME=seu_usuario
   KAGGLE_KEY=sua_chave
   ```

---

## 4. Configurar a Azure

### 4.1 Criar conta gratuita

Se ainda não tiver uma conta Azure, crie em [azure.microsoft.com/free](https://azure.microsoft.com/pt-br/free/). O tier gratuito é suficiente para este projeto.

### 4.2 Fazer login via Azure CLI

```bash
az login
```

Um navegador será aberto para autenticação. Após o login, liste suas assinaturas:

```bash
az account list --output table
```

Anote o valor da coluna `SubscriptionId` da assinatura que deseja usar.

### 4.3 Criar um Service Principal

O Terraform precisa de um Service Principal (identidade de serviço) para gerenciar recursos na Azure:

```bash
az ad sp create-for-rbac \
  --name "olist-platform-sp" \
  --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>
```

O comando retornará um JSON como este:

```json
{
  "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "displayName": "olist-platform-sp",
  "password": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

Preencha no `.env` mapeando os campos:

```bash
ARM_CLIENT_ID=<appId>
ARM_CLIENT_SECRET=<password>
ARM_SUBSCRIPTION_ID=<SUBSCRIPTION_ID>
ARM_TENANT_ID=<tenant>
```

---

## 5. Provisionar a infraestrutura com Terraform

Os arquivos Terraform estão em `infra/` e criam:
- **Resource Group** (`olist-rg-dev`)
- **Storage Account** com Hierarchical Namespace habilitado (Data Lake Gen2)
- **3 containers** para a arquitetura medalhão: `bronze`, `silver`, `gold`

### 5.1 Exportar credenciais para o ambiente

O provider AzureRM lê as variáveis `ARM_*` diretamente do ambiente:

```bash
export ARM_CLIENT_ID=$(grep ARM_CLIENT_ID .env | cut -d= -f2)
export ARM_CLIENT_SECRET=$(grep ARM_CLIENT_SECRET .env | cut -d= -f2)
export ARM_SUBSCRIPTION_ID=$(grep ARM_SUBSCRIPTION_ID .env | cut -d= -f2)
export ARM_TENANT_ID=$(grep ARM_TENANT_ID .env | cut -d= -f2)
```

Ou, se preferir, use o `source` com um helper:

```bash
set -a && source .env && set +a
```

### 5.2 Inicializar e aplicar

```bash
cd infra/

terraform init      # Baixa o provider AzureRM
terraform plan      # Mostra o que será criado (não altera nada)
terraform apply     # Cria os recursos na Azure (pedirá confirmação)
```

Digite `yes` quando solicitado. O processo leva cerca de 1–2 minutos.

### 5.3 Verificar os recursos criados

```bash
az resource list --resource-group olist-rg-dev --output table
```

Você deve ver a Storage Account e os containers `bronze`, `silver` e `gold`.

---

## 6. Configurar o Databricks Community Edition

### 6.1 Criar conta

1. Acesse [community.cloud.databricks.com](https://community.cloud.databricks.com)
2. Crie uma conta gratuita (Community Edition)

### 6.2 Gerar token de acesso

1. No workspace Databricks, clique no seu nome (canto superior direito) → **User Settings**
2. Vá em **Access Tokens → Generate New Token**
3. Dê um nome (ex: `olist-platform`) e clique em **Generate**
4. Copie o token gerado (ele só aparece uma vez)

### 6.3 Obter o HTTP Path do cluster

1. No menu lateral, vá em **Compute → seu cluster → Configuration → Advanced Options → JDBC/ODBC**
2. Copie o valor de **HTTP Path** (formato: `/sql/1.0/warehouses/...`)

### 6.4 Preencher o `.env`

```bash
DATABRICKS_HOST=https://community.cloud.databricks.com
DATABRICKS_TOKEN=<token gerado>
DATABRICKS_HTTP_PATH=<http path do cluster>
```

---

## 7. Subir o ambiente local com Docker

Com o `.env` preenchido, suba o contêiner:

```bash
make setup   # Constrói a imagem Docker (só precisa rodar uma vez)
make up      # Inicia o contêiner em background
make shell   # Abre um terminal dentro do contêiner
```

Para verificar se o ambiente está funcionando, dentro do shell do contêiner:

```bash
python -c "import pyspark; print('PySpark OK')"
dbt --version
```

---

## 8. Validar o CI localmente

Antes de abrir um Pull Request, rode as mesmas verificações que o GitHub Actions executa:

```bash
# Linting Python
ruff check .

# Testes unitários
pytest

# Validação do Terraform
cd infra/
terraform fmt -check -recursive
terraform validate
```

---

## Estrutura provisionada

Ao final desta fase, a seguinte infraestrutura estará disponível:

```
Azure
└── olist-rg-dev (Resource Group)
    └── olistdldevstr (Storage Account — Data Lake Gen2)
        ├── bronze/   ← dados brutos (Parquet/Delta)
        ├── silver/   ← dados limpos e padronizados
        └── gold/     ← dados modelados para analytics

Local
└── Docker (data_platform)
    ├── PySpark
    ├── dbt-databricks
    └── Streamlit (porta 8501)
```

---

## Próxima fase

Com a infraestrutura pronta, o próximo passo é configurar o pipeline de ingestão de dados:
→ [Fase 2 — Pipeline de Ingestão](./phase-02-ingestion.md) *(em breve)*
