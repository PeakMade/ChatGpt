# Azure Deployment Guide for ChatGPT Clone

## Prerequisites
1. Azure subscription
2. OpenAI API key
3. MongoDB Atlas account (optional, will use session storage if not configured)

## Deployment Steps

### 1. Create Azure App Service
```bash
# Using Azure CLI
az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name ChatGPT --runtime "PYTHON|3.11"
```

### 2. Configure Application Settings
In Azure Portal → Your App Service → Configuration → Application Settings, add:

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key

**Optional:**
- `MONGODB_URI`: MongoDB Atlas connection string (format: mongodb+srv://user:pass@cluster.mongodb.net/db)

### 3. Configure Startup Command
In Azure Portal → Your App Service → Configuration → General Settings:
- **Startup Command**: `python startup.py`

### 4. Deploy Code
Option A - GitHub Actions (Recommended):
- Connect your GitHub repository to Azure App Service
- The existing workflow will handle deployment

Option B - Azure CLI:
```bash
az webapp deployment source config --name ChatGPT --resource-group myResourceGroup --repo-url https://github.com/PeakMade/ChatGpt --branch main --manual-integration
```

Option C - Local Git:
```bash
az webapp deployment source config-local-git --name ChatGPT --resource-group myResourceGroup
git remote add azure <deployment-url>
git push azure main
```

### 5. Monitor Deployment
- Check deployment logs in Azure Portal → Your App Service → Deployment Center
- View application logs in Azure Portal → Your App Service → Log stream

## Important Files for Azure
- `startup.py` - Main entry point for Azure
- `web.config` - IIS configuration for Windows App Service
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version specification
- `.streamlit/config.toml` - Streamlit configuration

## Environment Variables
Set these in Azure App Service Configuration:

```
OPENAI_API_KEY=sk-...your-openai-key...
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/database
```

## Troubleshooting

### Common Issues:
1. **Application Error**: Check startup command is set to `python startup.py`
2. **OpenAI Errors**: Verify OPENAI_API_KEY is set in Application Settings
3. **Streamlit Not Loading**: Ensure port 8000 is configured in startup.py
4. **MongoDB Errors**: App will fall back to session storage if MongoDB fails

### View Logs:
```bash
az webapp log tail --name ChatGPT --resource-group myResourceGroup
```

## Performance Tips
- Use MongoDB Atlas for persistence
- Set appropriate scaling rules
- Enable Application Insights for monitoring
- Use CDN for static assets if needed

## Security
- Never commit API keys to repository
- Use Azure Key Vault for sensitive data
- Enable HTTPS only
- Configure proper CORS settings
