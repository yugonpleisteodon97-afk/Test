# Railway Deployment Guide for Radar Application

This guide will help you deploy the Radar application to Railway, replacing your Docker setup.

## Prerequisites

- Railway account (https://railway.app)
- Git repository set up
- Railway API Token: `4e056c91-6301-425b-a231-ca29c5a725cf`

## Files Created for Railway

The following files have been created to support Railway deployment:

1. **Procfile** - Defines service start commands
2. **railway.toml** - Railway-specific configuration
3. **nixpacks.toml** - Build configuration
4. **.railwayignore** - Files to exclude from deployment

## Step 1: Set Up Railway Project via Dashboard

### 1.1 Create New Project

1. Go to https://railway.app
2. Click "New Project"
3. Choose "Deploy from GitHub repo" and connect your repository
4. Railway will create your main project

### 1.2 Add PostgreSQL Database

1. In your Railway project, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically provision the database
4. Note: The `DATABASE_URL` variable will be automatically available

### 1.3 Add Redis

1. Click "New Service" again
2. Select "Database" → "Redis"
3. Railway will provision Redis
4. Note: The `REDIS_URL` variable will be automatically available

## Step 2: Deploy Three Services from Same Repo

You need to create **3 separate services** from the same GitHub repository:

### Service 1: Web Application (Main Flask App)

1. Click "New Service" → "GitHub Repo"
2. Select your repository
3. **Service Settings:**
   - **Name:** `radar-web`
   - **Root Directory:** Leave empty (uses project root)
   - **Build Command:** Auto-detected from nixpacks.toml
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 "app:create_app()"`
4. **Generate Domain:** Enable public access (this will give you a URL like `radar-web.railway.app`)

### Service 2: Celery Worker

1. Click "New Service" → "GitHub Repo"
2. Select the **same repository**
3. **Service Settings:**
   - **Name:** `radar-worker`
   - **Root Directory:** Leave empty
   - **Start Command:** `celery -A app.extensions.celery worker --loglevel=info`
4. **Generate Domain:** Not needed (internal service)

### Service 3: Celery Beat

1. Click "New Service" → "GitHub Repo"
2. Select the **same repository**
3. **Service Settings:**
   - **Name:** `radar-beat`
   - **Root Directory:** Leave empty
   - **Start Command:** `celery -A app.extensions.celery beat --loglevel=info`
4. **Generate Domain:** Not needed (internal service)

## Step 3: Configure Environment Variables

Set these environment variables in **ALL THREE SERVICES** (web, worker, beat):

### Required Variables (Auto-provided by Railway)

```bash
# These are automatically available from your Postgres service
DATABASE_URL=${{Postgres.DATABASE_URL}}

# These are automatically available from your Redis service  
REDIS_URL=${{Redis.REDIS_URL}}
```

### Variables You Need to Set

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-a-secure-random-32-char-key>
JWT_SECRET_KEY=<generate-a-secure-random-32-char-key>
ENCRYPTION_KEY=<generate-a-secure-random-32-char-key>

# Celery (derived from Redis)
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/1
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/2

# CORS - Update with your actual Railway domain after deployment
ALLOWED_ORIGINS=https://radar-web.railway.app,https://your-custom-domain.com

# OAuth Credentials (if using OAuth)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
OAUTH_REDIRECT_URI=https://radar-web.railway.app/api/auth/oauth/callback

# API Keys for External Services
ALPHA_VANTAGE_API_KEY=your_key
FINNHUB_API_KEY=your_key
CRUNCHBASE_API_KEY=your_key
SIMILARWEB_API_KEY=your_key
NEWS_API_KEY=your_key
THE_NEWS_API_KEY=your_key
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_BEARER_TOKEN=your_token
SERPAPI_API_KEY=your_key

# Monitoring (optional)
SENTRY_DSN=your_sentry_dsn_if_using_sentry
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

### How to Set Variables in Railway:

1. Click on each service
2. Go to "Variables" tab
3. Click "Raw Editor" to paste all variables at once
4. Or click "New Variable" to add them one by one

### Generating Secure Keys

You can generate secure keys using Python:

```python
import secrets
print(secrets.token_urlsafe(32))
```

Run this three times to generate SECRET_KEY, JWT_SECRET_KEY, and ENCRYPTION_KEY.

## Step 4: Handle Database Migrations

After your web service is deployed:

1. Go to your `radar-web` service in Railway
2. Open the service and go to the "Settings" tab
3. Under "Deploy", update the start command to include migrations:

```bash
flask db upgrade && gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 "app:create_app()"
```

This will automatically run migrations before starting the server.

## Step 5: Handle File Storage

⚠️ **Important:** Railway's filesystem is ephemeral (resets on each deploy).

### For Reports and Charts Storage

You have two options:

#### Option A: Use Railway Volumes (Simple)

1. In your `radar-web` service, go to "Settings"
2. Scroll to "Volumes"
3. Click "New Volume"
4. Mount Path: `/app/storage`
5. Size: Choose appropriate size (e.g., 5GB)

This creates persistent storage that survives deployments.

#### Option B: Use Cloud Storage (Recommended for Production)

Integrate with cloud storage services:

- **AWS S3**
- **Google Cloud Storage**
- **Cloudflare R2**
- **DigitalOcean Spaces**

Update your report generation code to save to cloud storage instead of local filesystem.

## Step 6: Verify Deployment

### Check Service Health

1. **Web Service:**
   - Visit your Railway-generated URL
   - Should see your application running

2. **Celery Worker:**
   - Check logs in Railway dashboard
   - Should see: "celery@... ready"

3. **Celery Beat:**
   - Check logs in Railway dashboard
   - Should see beat scheduler running

### Monitor Logs

1. Go to each service in Railway
2. Click on "Deployments"
3. Click on the latest deployment
4. View real-time logs

### Test Database Connection

Your app will automatically connect using the `DATABASE_URL` variable provided by Railway.

## Step 7: Custom Domain (Optional)

1. Go to your `radar-web` service
2. Click "Settings"
3. Scroll to "Domains"
4. Click "Custom Domain"
5. Enter your domain and follow DNS configuration instructions

## Troubleshooting

### Common Issues

1. **Build Failures:**
   - Check build logs in Railway
   - Verify all requirements are in `requirements.txt`
   - Check nixpacks.toml configuration

2. **Database Connection Issues:**
   - Verify `DATABASE_URL` is set correctly
   - Check if PostgreSQL service is running
   - The config.py has been updated to handle postgres:// vs postgresql:// prefix

3. **Celery Not Working:**
   - Verify Redis is running
   - Check that CELERY_BROKER_URL and CELERY_RESULT_BACKEND are set
   - Verify all three services share the same environment variables

4. **Port Issues:**
   - Railway automatically provides $PORT variable
   - config.py has been updated to use PORT environment variable

### View Logs

```bash
# If you install Railway CLI:
railway logs --service radar-web
railway logs --service radar-worker
railway logs --service radar-beat
```

## Comparison: Docker vs Railway

| Feature | Docker Compose | Railway |
|---------|---------------|---------|
| **Setup** | `docker-compose up` | Push to Git |
| **Scaling** | Manual containers | Click to scale |
| **Database** | Self-managed | Managed service |
| **Redis** | Self-managed | Managed service |
| **Logs** | `docker logs` | Built-in dashboard |
| **SSL/HTTPS** | Manual setup | Automatic |
| **Backups** | Manual | Automatic (DB) |
| **Cost** | Infrastructure | Pay-as-you-go |

## Cost Estimation

Railway offers:
- **Hobby Plan:** $5/month + usage
- **Pro Plan:** $20/month + usage

Typical usage for this app:
- PostgreSQL: ~$5-10/month
- Redis: ~$2-5/month  
- Web + Workers: ~$10-20/month
- **Total:** ~$20-40/month

## Next Steps

1. ✅ Push your code to GitHub (with the new Railway files)
2. ✅ Create Railway project and add services
3. ✅ Configure environment variables
4. ✅ Deploy and verify each service
5. ✅ Set up custom domain (optional)
6. ✅ Configure monitoring and alerts

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app

---

Your application is now ready to deploy to Railway! 🚀
