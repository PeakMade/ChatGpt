# Deployment Troubleshooting Guide

## Common Application Errors and Solutions

### 1. Missing Dependencies Error
**Error**: ImportError or ModuleNotFoundError
**Solution**: Ensure all dependencies are in requirements.txt:
```
psycopg2-binary>=2.9.0,<3.0.0
cryptography>=41.0.0,<42.0.0
```

### 2. Database Connection Error
**Error**: "could not connect to server" or "database connection failed"
**Solution**: Set the DATABASE_URL environment variable:
```
DATABASE_URL=postgresql://username:password@hostname:5432/database_name
```

### 3. OpenAI API Key Error
**Error**: "Authentication failed" or "No API key provided"
**Solution**: Set the OPENAI_API_KEY environment variable:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. Secret Key Error
**Error**: "SECRET_KEY must be set"
**Solution**: Set a secure secret key:
```
SECRET_KEY=your-super-secure-random-secret-key
```

### 5. Port Binding Error
**Error**: "Permission denied" or "Address already in use"
**Solution**: Ensure the PORT environment variable is set correctly:
```
PORT=5000
```

## Deployment Platform Specific Instructions

### Heroku
1. Add PostgreSQL addon: `heroku addons:create heroku-postgresql:mini`
2. Set environment variables:
   ```
   heroku config:set OPENAI_API_KEY=your-key
   heroku config:set SECRET_KEY=your-secret
   heroku config:set FLASK_ENV=production
   ```

### Azure App Service
1. Create PostgreSQL database in Azure
2. Set environment variables in Configuration > Application Settings
3. Ensure connection strings are properly formatted

### Railway/Render
1. Connect PostgreSQL database
2. Set environment variables in dashboard
3. Ensure build commands are correct

## Debugging Steps
1. Check deployment logs for specific error messages
2. Verify all environment variables are set
3. Test database connectivity
4. Verify OpenAI API key is valid
5. Check if all files are included in deployment

## Environment Variables Checklist
- [ ] OPENAI_API_KEY
- [ ] DATABASE_URL
- [ ] SECRET_KEY
- [ ] FLASK_ENV=production
- [ ] FLASK_DEBUG=false
- [ ] PORT (if required by platform)
