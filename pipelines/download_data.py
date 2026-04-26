import os
import subprocess
import zipfile
import shutil
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Configurações
DATASET = "olistbr/brazilian-ecommerce"
TEMP_DIR = Path("data/raw")
BRONZE_DIR = Path("data/bronze")

def load_rules():
    """Carrega regras da AI Validation Layer"""
    try:
        with open("ml_ops/validation_layer/rules.yaml", "r") as f:
            rules = yaml.safe_load(f)
            return rules.get("rules", [])
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível carregar as regras de validação. {e}")
        return []

def get_allowed_tables(rules):
    for rule in rules:
        if isinstance(rule, dict) and "allowed_tables" in rule:
            return rule["allowed_tables"]
    return None

def main():
    print(f"🚀 Iniciando Pipeline de Ingestão (Fase 2)")
    
    # 1. Criar diretório temporário
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # 2. Baixar os dados usando a API do Kaggle
    print(f"📦 Baixando dataset '{DATASET}' do Kaggle...")
    try:
        subprocess.run(["kaggle", "datasets", "download", "-d", DATASET, "-p", str(TEMP_DIR)], check=True)
    except subprocess.CalledProcessError:
        print("❌ Erro ao baixar o dataset. Verifique as credenciais do Kaggle no arquivo .env.")
        return
    
    # 3. Extrair os arquivos zipados
    zip_path = TEMP_DIR / "brazilian-ecommerce.zip"
    if zip_path.exists():
        print(f"📂 Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(TEMP_DIR)
        os.remove(zip_path) # Apaga o .zip para poupar espaço
    else:
        print("❌ Arquivo zip não encontrado.")
        return
    
    # 4. (Governança) Carregar tabelas permitidas
    rules = load_rules()
    allowed_tables = get_allowed_tables(rules)
    
    print(f"☁️ Iniciando movimentação para o Data Lake Local ({BRONZE_DIR})...")
    
    # 5. Criar diretório Bronze
    os.makedirs(BRONZE_DIR, exist_ok=True)
    
    # 6. Mover os CSVs extraídos para a camada Bronze
    success_count = 0
    for file in os.listdir(TEMP_DIR):
        if file.endswith(".csv"):
            # Olist tem nomes como olist_orders_dataset.csv
            table_name = file.replace("olist_", "").replace("_dataset", "").replace(".csv", "")
            
            # Validação via AI Validation Layer
            if allowed_tables and table_name not in allowed_tables:
                print(f"⏭️  Ignorando arquivo '{file}': A tabela '{table_name}' não está mapeada nas regras da Governança.")
                continue
                
            local_file = TEMP_DIR / file
            bronze_file = BRONZE_DIR / file
            print(f"⬆️  [Governança: Aprovado] Movendo {file} para a Bronze Layer...")
            
            # Movendo o arquivo para a camada Bronze
            try:
                shutil.move(str(local_file), str(bronze_file))
                success_count += 1
            except Exception as e:
                print(f"❌ Erro ao enviar {file}: {e}")
                
    # 7. Limpeza
    print("🧹 Limpando arquivos temporários locais...")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    
    print(f"✅ Ingestão finalizada! {success_count} tabelas foram enviadas com sucesso para a camada Bronze.")

if __name__ == "__main__":
    main()
