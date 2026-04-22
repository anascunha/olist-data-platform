# Criação do Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "${var.prefix}-rg-${var.environment}"
  location = var.location
}

# Criação da Storage Account (Configurada para Data Lake Gen2 - Tier Padrão e mais barato)
resource "azurerm_storage_account" "datalake" {
  name                     = "${var.prefix}dl${var.environment}str"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true # Habilita o Hierarchical Namespace para Data Lake Gen2

  tags = {
    environment = var.environment
    project     = "olist-platform"
  }
}

# Containers para a Arquitetura Medalhão
resource "azurerm_storage_data_lake_gen2_filesystem" "bronze" {
  name               = "bronze"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "silver" {
  name               = "silver"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "gold" {
  name               = "gold"
  storage_account_id = azurerm_storage_account.datalake.id
}
