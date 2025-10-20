# Azure ML Deployment Guide: Retrieval-Augmented QA Pipeline

This guide documents the steps to deploy a **Retrieval-Augmented QA (RAG)** model on **Azure Machine Learning (Azure ML)**, including CLI commands, common issues, and solutions. It covers everything from authentication to online deployment.

---

## 1. Prerequisites

- Azure CLI installed and updated (`az --version`)
- Azure ML CLI extension installed:
  ```bash
  az extension add -n ml
- Python >= 3.8
- Docker installed and running (for custom container images)
- Access to an Azure subscription with sufficient quota for the desired VM type

## 2. Login and Workspace Setup
```bash
# Login to Azure
az login

# List available subscriptions
az account list --output table

# Set subscription
az account set --subscription <your-subscription-id>

# Verify ML workspace exists
az ml workspace show --resource-group <resource-group> --name <workspace-name>
```

## 3. Check Compute Quotas

Before deploying, check the current quota for VM types:
```bash
# List vCPU usage and limits
az vm list-usage --location <region> --output table
```
Common Issue:
- Deployment fails with “Not enough quota” even if online portal shows availability.
- Reason: Azure ML maintains separate compute quotas per endpoint type. CLI may report 0/0 for quota.

Solution:
- Submit a quota increase via **Azure Portal → Help + Support → New support request → Quota**.
- Wait for approval before deploying compute-intensive endpoints (e.g., DSv4 Family).

## 4. Create Azure ML Environment

**Option A**: Use an existing Docker image
```bash
az ml environment create \
  --name ragqa-env \
  --docker-image <container-registry>/<image-name>:latest
```
Note: Make sure the image name is correct in ACR. Mistakes here will lead to `unrecognized arguments`.

## 5. Define the Deployment (deployment.yaml)
```yaml
$schema: https://azuremlschemas.azureedge.net/latest/onlineDeployment.schema.json
name: rag-qa-deployment
endpoint_name: rag-qa-endpoint
# Use the 'image' field here for a custom container
environment: 
  image: ragqaacr.azurecr.io/rag-qa:latest

code_configuration:
  code: ./src
  scoring_script: serve.py

instance_type: Standard_DS3_v2
instance_count: 1
```

Important:
- Minimum recommended SKU for general-purpose endpoints: DSv3/DSv4 family.
- Using unsupported/insufficient SKU (e.g., Standard_DS2_v2) may result in:
```arduino
BadRequest: Not enough quota available
```

## 6. Create the Online Endpoint
```bash
az ml online-endpoint create \
  --name rag-qa-endpoint \
  --resource-group <resource-group> \
  --workspace-name <workspace-name>
```

Common Issue: Endpoint exists error

Solution:
- Delete existing endpoint:
```bash
az ml online-endpoint delete \
  --name rag-qa-endpoint \
  --resource-group <resource-group> \
  --workspace-name <workspace-name> \
  --yes
```

## 7. Deploy the Model
```bash
az ml online-deployment create \
  --file deployment.yaml \
  --resource-group <resource-group> \
  --workspace-name <workspace-name>
```

Common Issues:
1. Insufficient Quota / Wrong VM type
  - Check quota: `az vm list-usage --location <region> --output table`
  - Use an approved VM type and submit quota increase if needed.
2. Environment missing Docker image
  - Ensure Docker image exists in ACR and environment references it correctly.
3. Endpoint in use
  - Delete deployment or endpoint before redeploying.

## **NOTE** I wasn't able to do this because my requests for more quotas kept getting denied. They prioritize business over developers.
## 8. Testing the Endpoint
```bash
az ml online-endpoint invoke \
  --name rag-qa-endpoint \
  --resource-group <resource-group> \
  --workspace-name <workspace-name> \
  --request-file test_request.json
```
- `test_request.json` should contain your input prompt for the RAG model.

## 9. Clean Up Resources

To free up vCPUs or remove deployments:
```bash
# Delete a deployment
az ml online-deployment delete \
  --name rag-qa-deployment \
  --endpoint-name rag-qa-endpoint \
  --resource-group <resource-group> \
  --workspace-name <workspace-name> \
  --yes

# Delete an endpoint
az ml online-endpoint delete \
  --name rag-qa-endpoint \
  --resource-group <resource-group> \
  --workspace-name <workspace-name> \
  --yes
```

## 10. Notes And Lessons Learned

1. Quotas in CLI vs Portal: CLI can show 0/0 even when portal shows limits — double-check in portal.
2. VM SKU Recommendations: Always check [Azure ML Online Endpoint SKUs](https://learn.microsoft.com/en-us/azure/machine-learning/reference-managed-online-endpoints-vm-sku-list?view=azureml-api-2)
3. Environment Image Issues: Misnaming Docker image or failing to push to ACR will block deployments.
4. B-Series Temporary Deployment: If used for testing, remember to delete the deployment to free vCPU quota.









