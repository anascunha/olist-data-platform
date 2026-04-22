import os
from kaggle.api.kaggle_api_extended import KaggleApi


def download_olist_dataset(download_path="data/raw"):
    """
    Downloads the Olist dataset from Kaggle to the specified path.
    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables to be set.
    """
    os.makedirs(download_path, exist_ok=True)

    try:
        # Inicializa e autentica via variáveis de ambiente
        api = KaggleApi()
        api.authenticate()

        dataset_name = "olistbr/brazilian-ecommerce"
        print(f"Iniciando download do dataset '{dataset_name}' para '{download_path}'...")

        # Faz o download e extrai o arquivo ZIP
        api.dataset_download_files(dataset_name, path=download_path, unzip=True)
        print("✅ Download e extração concluídos com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao baixar o dataset: {e}")
        print("Certifique-se de que as variáveis KAGGLE_USERNAME e KAGGLE_KEY estão configuradas no .env ou no sistema.")

if __name__ == "__main__":
    download_olist_dataset()
