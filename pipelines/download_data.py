"""
Fase 2 — Ingestão do dataset Olist (Kaggle) para o Volume de landing no Unity Catalog.

Fluxo:
    1. Download do dataset via Kaggle CLI          -> data/raw/
    2. Extração do .zip
    3. Governança (AI Validation Layer)            -> apenas tabelas em allowed_tables
    4. Landing local                               -> data/landing/olist/
    5. Upload via Databricks CLI                   -> /Volumes/raw/source_olist/landing/
    6. Limpeza do diretório temporário

A conversão dos CSVs em tabelas Delta (raw.source_olist.*) é feita pelo notebook
databricks/ingestao_bronze.py.
"""

import argparse
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import yaml
from dotenv import load_dotenv

from pipelines.config import volume_path
from pipelines.utils import get_allowed_tables, table_name_from_file

# Carregar variáveis de ambiente do .env
load_dotenv()

# Configurações
DATASET = "olistbr/brazilian-ecommerce"
TEMP_DIR = Path("data/raw")
LANDING_DIR = Path("data/landing/olist")
RULES_PATH = Path("ml_ops/validation_layer/rules.yaml")


def load_rules(path=RULES_PATH):
    """Carrega regras da AI Validation Layer"""
    try:
        with open(path, "r") as f:
            rules = yaml.safe_load(f)
            return rules.get("rules", [])
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível carregar as regras de validação. {e}")
        return []


def download_dataset(temp_dir=TEMP_DIR):
    """Baixa o dataset do Kaggle e extrai o .zip. Retorna True em caso de sucesso."""
    os.makedirs(temp_dir, exist_ok=True)

    print(f"📦 Baixando dataset '{DATASET}' do Kaggle...")
    try:
        subprocess.run(
            ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(temp_dir)], check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Erro ao baixar o dataset. Verifique as credenciais do Kaggle no arquivo .env.")
        return False

    zip_path = Path(temp_dir) / "brazilian-ecommerce.zip"
    if not zip_path.exists():
        print("❌ Arquivo zip não encontrado.")
        return False

    print("📂 Extraindo arquivos...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)
    os.remove(zip_path)  # Apaga o .zip para poupar espaço
    return True


def stage_allowed_files(temp_dir, landing_dir, allowed_tables):
    """Move para a landing local apenas os CSVs autorizados pela governança."""
    os.makedirs(landing_dir, exist_ok=True)

    moved = []
    for file in sorted(os.listdir(temp_dir)):
        if not file.endswith(".csv"):
            continue

        table_name = table_name_from_file(file)
        if allowed_tables and table_name not in allowed_tables:
            print(f"⏭️  Ignorando '{file}': a tabela '{table_name}' não está mapeada na Governança.")
            continue

        print(f"✅ [Governança: Aprovado] {file} -> {landing_dir}")
        shutil.move(str(Path(temp_dir) / file), str(Path(landing_dir) / file))
        moved.append(file)
    return moved


def upload_to_volume(local_dir, target_volume):
    """Envia os CSVs para o Volume do Unity Catalog usando a Databricks CLI."""
    print(f"☁️  Enviando {local_dir} -> dbfs:{target_volume}")
    try:
        subprocess.run(
            [
                "databricks", "fs", "cp", "--recursive", "--overwrite",
                str(local_dir), f"dbfs:{target_volume}",
            ],
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Erro no upload. Verifique a Databricks CLI (`databricks auth profiles`).")
        return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ingestão Olist -> Unity Catalog Volume")
    parser.add_argument(
        "--skip-upload", action="store_true", help="Mantém os CSVs apenas em data/landing/olist"
    )
    args = parser.parse_args(argv)

    print("🚀 Iniciando Pipeline de Ingestão (Fase 2)")

    if not download_dataset(TEMP_DIR):
        return 1

    allowed_tables = get_allowed_tables(load_rules())
    moved = stage_allowed_files(TEMP_DIR, LANDING_DIR, allowed_tables)

    print("🧹 Limpando arquivos temporários locais...")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    if not args.skip_upload and not upload_to_volume(LANDING_DIR, volume_path("olist")):
        return 1

    print(f"✅ Ingestão finalizada! {len(moved)} tabelas disponíveis na landing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
