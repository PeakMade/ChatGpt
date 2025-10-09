# TTL Configuration Guide

## Current Maximum TTL Settings

### 1. User Session TTL: 60 Days
- **Duration**: 5,184,000 seconds (60 days)
- **What it means**: Users stay logged in for 60 days without needing to refresh
- **Environment variable**: `SESSION_LIFETIME` (in seconds)

### 2. HTTP Request Timeout: 30 Minutes  
- **Duration**: 1,800 seconds (30 minutes)
- **What it means**: Individual requests (like AI responses) can take up to 30 minutes
- **Configuration**: Set in Procfile `--timeout 1800`

## Environment Variable Options

You can override the session lifetime by setting the `SESSION_LIFETIME` environment variable:

```bash
# Examples:
SESSION_LIFETIME=86400      # 24 hours
SESSION_LIFETIME=604800     # 7 days  
SESSION_LIFETIME=2592000    # 30 days
SESSION_LIFETIME=5184000    # 60 days (current setting)
SESSION_LIFETIME=31536000   # 1 year (maximum)
```

## TTL Limits by Deployment Platform

### Local Development
- **Session TTL**: No limit (can set to 1 year+)
- **Request Timeout**: No practical limit

### Heroku  
- **Session TTL**: 30 days (app sleeps after 30 min inactivity)
- **Request Timeout**: 30 seconds HARD LIMIT (ignores your timeout setting)

### Railway
- **Session TTL**: 30 days
- **Request Timeout**: 10 minutes maximum

### Render
- **Session TTL**: 30 days  
- **Request Timeout**: 15 minutes maximum

### Azure App Service
- **Session TTL**: 30 days
- **Request Timeout**: 30 minutes maximum

## Extreme TTL Settings (Maximum Possible)

If you want to push to absolute limits:

### Session Lifetime (app.py)
```python
# 1 year maximum practical
app.config['PERMANENT_SESSION_LIFETIME'] = 31536000  # 1 year

# 10 years (extreme, not recommended)
app.config['PERMANENT_SESSION_LIFETIME'] = 315360000  # 10 years
```

### Request Timeout (Procfile)
```
# Maximum for most platforms
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 3600  # 1 hour

# Extreme (may cause platform issues)
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 7200  # 2 hours
```

## Security Considerations

**Long Session TTLs (60 days+):**
- ✅ Excellent user experience (no re-login for 2 months)
- ⚠️ Higher security risk if device compromised
- ⚠️ More server memory usage for session storage

**Long Request Timeouts (30+ minutes):**
- ✅ Handles very complex AI queries
- ⚠️ Server resources tied up longer
- ⚠️ May hit platform limits

## Recommendations

### For Production Use:
- **Session TTL**: 7-30 days (good balance)
- **Request Timeout**: 5-15 minutes (sufficient for most AI responses)

### For Development/Testing:
- **Session TTL**: 30 days (convenient)
- **Request Timeout**: 30 minutes (handles long debugging sessions)

### Current Settings (Extended for Better UX):
- **Session TTL**: ✅ 60 days (5,184,000 seconds)
- **Request Timeout**: ✅ 30 minutes (1,800 seconds)
- **Conversation Recall**: ✅ 25 conversations (extended from default)

**These settings provide excellent user experience with extended recall capabilities!**
