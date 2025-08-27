# Azure Cosmos DB Setup Guide

## Quick Setup for Azure Cosmos DB

### 1. Create Azure Cosmos DB Account
1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Azure Cosmos DB"
4. Click "Create"

### 2. Configure Cosmos DB
1. **Subscription**: Choose your Azure subscription
2. **Resource Group**: Create new or use existing
3. **Account Name**: Choose a unique name (e.g., "myapp-cosmos")
4. **API**: Select "Core (SQL)" - Recommended
5. **Location**: Choose region closest to you
6. **Capacity mode**: Select "Provisioned throughput"
7. **Free Tier**: Enable if available (400 RU/s free)
8. Click "Review + Create"

### 3. Get Connection Details
1. Once created, go to your Cosmos DB account
2. In the left menu, click "Keys"
3. Copy the following:
   - **URI** (Primary endpoint)
   - **PRIMARY KEY**

### 4. Configure Your App
1. Open the `.env` file in your project
2. Replace the placeholders:
   ```
   COSMOS_ENDPOINT=https://your-account-name.documents.azure.com:443/
   COSMOS_KEY=your-very-long-primary-key-here
   ```

### 5. Install Dependencies
Run in your terminal:
```bash
pip install azure-cosmos
```

### 6. Restart Your App
After adding the Cosmos DB connection details, restart your Streamlit app to see the connection success message.

## Benefits of Azure Cosmos DB vs MongoDB:
- ✅ **Integrated with Azure** - Same ecosystem as your App Service
- ✅ **Free Tier** - 400 RU/s + 25GB storage forever
- ✅ **Auto-scaling** - Handles traffic spikes automatically
- ✅ **Global distribution** - Can replicate worldwide
- ✅ **Multiple APIs** - SQL, MongoDB, Cassandra, etc.
- ✅ **SLA guarantee** - 99.999% availability

## Note: App Works Without Cosmos DB
The app will work perfectly fine without Cosmos DB - it just won't save conversations between sessions. Cosmos DB is only needed if you want persistent conversation storage.
