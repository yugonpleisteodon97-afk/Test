# Railway Deployment - Quick Start Guide

This is a quick reference guide for deploying the Radar application to Railway.

## 📋 What's Changed

We've migrated from Docker to Railway. Here are the new files:

- ✅ `Procfile` - Service definitions
- ✅ `railway.toml` - Railway configuration
- ✅ `nixpacks.toml` - Build settings
- ✅ `.railwayignore` - Deployment exclusions
- ✅ `env.railway.example` - Environment variables template
- ✅ `generate_railway_keys.py` - Secure key generator
- ✅ `RAILWAY_DEPLOYMENT.md` - Full deployment guide

## 🚀 Quick Deployment Steps

### 1. Generate Secure Keys

```bash
python generate_railway_keys.py
```

Save the output - you'll need these keys!

### 2. Push to GitHub

```bash
git add .
git commit -m "Configure for Railway deployment"
git push origin main
```

### 3. Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Connect your repository

### 4. Add Databases

**Add PostgreSQL:**
- Click "New Service" → "Database" → "PostgreSQL"

**Add Redis:**
- Click "New Service" → "Database" → "Redis"

### 5. Deploy Three Services

Create three services from the same repository:

**Service 1: Web App**
- Name: `radar-web`
- Start Command: (uses Procfile automatically)
- Enable "Generate Domain"

**Service 2: Celery Worker**
- Name: `radar-worker`
- Start Command: `celery -A app.extensions.celery worker --loglevel=info`

**Service 3: Celery Beat**
- Name: `radar-beat`
- Start Command: `celery -A app.extensions.celery beat --loglevel=info`

### 6. Set Environment Variables

For **each service** (web, worker, beat), add these variables:

```bash
# Auto-provided by Railway
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/1
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/2

# Your generated keys
SECRET_KEY=<from-generate_railway_keys.py>
JWT_SECRET_KEY=<from-generate_railway_keys.py>
ENCRYPTION_KEY=<from-generate_railway_keys.py>

# App config
FLASK_ENV=production
ALLOWED_ORIGINS=https://your-domain.railway.app

# Add your API keys (see env.railway.example)
```

### 7. Deploy!

Railway will automatically deploy when you push to GitHub.

## 📊 Service Architecture

```
┌─────────────────┐
│   PostgreSQL    │ ←─┐
│   (Managed)     │   │
└─────────────────┘   │
                      │
┌─────────────────┐   │
│      Redis      │ ←─┼─┐
│   (Managed)     │   │ │
└─────────────────┘   │ │
                      │ │
┌─────────────────┐   │ │
│   radar-web     │ ──┘ │
│ (Flask + Gunicorn)   │
│  PORT: Auto     │     │
└─────────────────┘     │
                        │
┌─────────────────┐     │
│  radar-worker   │ ────┘
│ (Celery Worker) │
└─────────────────┘
                        
┌─────────────────┐
│  radar-beat     │
│ (Celery Beat)   │
└─────────────────┘
```

## 🔍 Monitoring

**View Logs:**
1. Go to Railway Dashboard
2. Click on service name
3. View real-time logs in "Deployments" tab

**Check Status:**
- All services should show "Active" status
- Green indicators mean healthy services

## 🛠️ Troubleshooting

### Build Fails
- Check `requirements.txt` is up to date
- View build logs in Railway Dashboard

### Database Connection Issues
- Verify PostgreSQL service is running
- Check `DATABASE_URL` variable is set

### Celery Not Processing Tasks
- Verify Redis is running
- Check worker logs for errors
- Ensure all services have same environment variables

## 📚 More Information

For detailed deployment instructions, see:
- `RAILWAY_DEPLOYMENT.md` - Complete deployment guide
- `env.railway.example` - All environment variables

## 💡 Key Differences from Docker

| Docker | Railway |
|--------|---------|
| `docker-compose up` | Automatic deployment |
| Manual scaling | Click to scale |
| Self-managed DB | Managed PostgreSQL |
| Local logs | Cloud dashboard |
| Manual SSL | Automatic HTTPS |

## 🆘 Need Help?

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Full Guide: See `RAILWAY_DEPLOYMENT.md`

---

Your Radar app is ready for Railway! 🎉
