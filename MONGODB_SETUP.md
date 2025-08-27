# MongoDB Setup Guide

## Quick Setup for MongoDB Atlas (Free Tier)

### 1. Create MongoDB Atlas Account
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Click "Try Free"
3. Create your account

### 2. Create a Free Cluster
1. Choose "Create a deployment"
2. Select "M0 Sandbox" (Free forever)
3. Choose your preferred cloud provider and region
4. Click "Create Deployment"

### 3. Create Database User
1. In the Security section, click "Database Access"
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Enter username and password (save these!)
5. Select "Read and write to any database"
6. Click "Add User"

### 4. Configure Network Access
1. In the Security section, click "Network Access"
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (for development)
4. Click "Confirm"

### 5. Get Connection String
1. Go to "Database" section
2. Click "Connect" on your cluster
3. Select "Connect your application"
4. Copy the connection string
5. Replace `<password>` with your database user password

### 6. Add to Your App
1. Open the `.env` file in your project
2. Replace `your_mongodb_connection_string_here` with your actual connection string
3. It should look like:
   ```
   MONGODB_URI=mongodb+srv://myuser:mypassword@cluster0.abc123.mongodb.net/chatgpt_clone?retryWrites=true&w=majority
   ```

### 7. Restart Your App
After adding the MongoDB connection string, restart your Streamlit app to see the connection success message.

## Note: App Works Without MongoDB
The app will work perfectly fine without MongoDB - it just won't save conversations between sessions. MongoDB is only needed if you want persistent conversation storage.
