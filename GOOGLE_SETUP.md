# Google Cloud Setup for Documetor

This guide walks you through setting up your Google Cloud environment for use with Documetor.

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "documentor-project")
5. Click "Create"
6. Wait for the project to be created and then select it

## 2. Enable Required APIs

You need to enable several APIs for Documetor to work properly:

1. Go to [API Library](https://console.cloud.google.com/apis/library)
2. Search for and enable each of the following APIs:
   - Vertex AI API
   - Cloud Storage API
   - Vertex AI Matching Engine API

For each API:
1. Click on the API in the search results
2. Click "Enable"
3. Wait for the API to be enabled (may take a few minutes)

## 3. Create a Service Account

1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "Create Service Account"
3. Enter a service account name (e.g., "documentor-service")
4. Add a description: "Service account for Documetor document embedding"
5. Click "Create and Continue"

## 4. Assign Required Roles

Assign the following roles to your service account:

1. In the "Grant this service account access to project" section, add the following roles:
   - Vertex AI User
   - Storage Admin
   - Vertex AI Matching Engine Admin

2. Click "Continue"
3. Skip the "Grant users access to this service account" section
4. Click "Done"

## 5. Create and Download Service Account Key

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" and select "Create new key"
4. Select "JSON" as the key type
5. Click "Create"
6. The key file will be automatically downloaded to your computer
7. Keep this file secure – it grants access to your Google Cloud resources

## 6. Set Up Authentication for Local Development

### Linux/macOS:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
```

To make this persistent, add it to your `~/.bashrc` or `~/.zshrc` file:

```bash
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"' >> ~/.bashrc
source ~/.bashrc
```

### Windows:

Using Command Prompt:
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your-service-account-key.json
```

Using PowerShell:
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your-service-account-key.json"
```

For persistent setup in Windows, add it to your system environment variables:
1. Search for "Environment Variables" in Windows search
2. Click "Edit the system environment variables"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `GOOGLE_APPLICATION_CREDENTIALS`
6. Variable value: `C:\path\to\your-service-account-key.json`
7. Click "OK" on all dialogs

## 7. Set Up a Storage Bucket (Optional)

If you're using the Vertex Matching Engine store, you'll need a Cloud Storage bucket:

1. Go to [Cloud Storage > Buckets](https://console.cloud.google.com/storage/browser)
2. Click "Create Bucket"
3. Enter a globally unique bucket name (e.g., `your-project-id-matching-engine`)
4. Choose a region (should match the region you'll use for Vertex AI)
5. Leave other settings as default
6. Click "Create"

## 8. Configure Vertex AI Matching Engine (For Production Use)

For production deployments using Vertex Matching Engine:

1. Go to [Vertex AI > Matching Engine](https://console.cloud.google.com/vertex-ai/matching-engine)
2. Click "Enable" if prompted

Documetor will create the necessary indexes and endpoints automatically, but you may want to review these settings:

1. Go to "Indexes" tab to view your created indexes
2. Go to "Index endpoints" tab to view the deployed endpoints

## 9. Quota and Billing Considerations

Vertex AI services are not free. Ensure your billing is set up correctly:

1. Go to [Billing](https://console.cloud.google.com/billing)
2. Ensure your project is linked to a billing account

Consider setting up budget alerts:
1. Go to [Budgets & Alerts](https://console.cloud.google.com/billing/budgets)
2. Click "Create Budget"
3. Follow the steps to set a budget and alert thresholds

### Quotas

You may need to request quota increases for:
- Vertex AI API requests
- Vertex AI Embedding API requests
- Matching Engine operations

To check and adjust quotas:
1. Go to [Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. Filter by "Vertex AI"
3. Select the quota you want to modify
4. Click "Edit Quotas" to request an increase

## 10. Verify Your Setup

Verify your setup with this simple test:

```python
from google.cloud import storage
from google.cloud import aiplatform

# Initialize clients
storage_client = storage.Client()
ai_client = aiplatform.init()

# List buckets (to test Storage API)
buckets = list(storage_client.list_buckets())
print(f"Storage API works! Found {len(buckets)} buckets.")

# List Vertex AI models (to test Vertex AI API)
models = aiplatform.Model.list()
print(f"Vertex AI API works! Found {len(models)} models.")

print("Setup verified successfully!")
```

## Troubleshooting

### Authentication Issues

**Problem**: `Could not automatically determine credentials`
**Solution**: Check that your environment variable is correctly set:
```bash
# Linux/macOS
echo $GOOGLE_APPLICATION_CREDENTIALS

# Windows PowerShell
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```

**Problem**: `Permission denied` errors
**Solution**: Verify that your service account has the correct roles assigned. You may need to add additional roles depending on the specific operations you're performing.

### API Errors

**Problem**: `API not enabled` errors
**Solution**: Double-check that you've enabled all required APIs. The error message will specify which API needs to be enabled.

### Quota Errors

**Problem**: `Quota exceeded` errors
**Solution**: Request a quota increase as described in the "Quota and Billing Considerations" section.

### Region Issues

**Problem**: Resources not found across regions
**Solution**: Ensure all your resources (Vertex AI endpoints, Storage buckets, etc.) are in the same region. You can specify the region when initializing Documetor:

```python
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    location="us-central1"  # Ensure this matches your resources
)
```

## Cost Optimization Tips

1. **Use local storage for development**:
   ```python
   # Use local storage during development to avoid Matching Engine costs
   embedder = DocumentEmbedder(
       project_id="your-gcp-project-id",
       store_type="local"
   )
   ```

2. **Batch processing**:
   Process documents in batches to minimize API calls.

3. **Right-size your Matching Engine**:
   Choose appropriate configurations based on your data size and query volume.

4. **Clean up unused resources**:
   Delete unused indexes and endpoints to avoid ongoing charges.
