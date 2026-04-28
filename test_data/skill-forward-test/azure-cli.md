# Azure CLI

## Login with device code
```bash
az login --use-device-code
```

## Select a subscription
```bash
az account set --subscription "<subscription-name>"
```

## List storage accounts in a resource group
```bash
az storage account list --resource-group <resource-group> --output table
```

## List containers in a storage account
```bash
# Assumes login-based auth already works in the current shell
az storage container list --account-name <storage-account> --auth-mode login --output table
```

## Download blobs from a container
```bash
# Assumes login-based auth already works in the current shell
az storage blob download-batch \
  --account-name <storage-account> \
  --auth-mode login \
  --source <container-name> \
  --destination ./downloads
```
