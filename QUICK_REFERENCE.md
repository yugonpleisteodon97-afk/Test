# Railway Deployment - Quick Reference Card

## 🎯 Essential Information

**Railway Dashboard:** https://railway.app  
**API Token:** `4e056c91-6301-425b-a231-ca29c5a725cf`

## 📋 Pre-Deployment Checklist

- [ ] Run `python verify_railway_setup.py` (all checks pass)
- [ ] Run `python generate_railway_keys.py` (save the keys!)
- [ ] Commit changes: `git add . && git commit -m "Configure for Railway"`
- [ ] Push to GitHub: `git push origin main`

## 🚀 Deployment Steps (In Order)

### 1️⃣ Create Railway Project
```
1. Go to railway.app
2. New Project → Deploy from GitHub
3. Select your Radar repository
```

### 2️⃣ Add Databases
```
Add PostgreSQL:  New Service → Database → PostgreSQL
Add Redis:       New Service → Database → Redis
```

### 3️⃣ Configure Main Web Service
```
Service Name: radar-web
Settings → Generate Domain: ENABLE
(This creates automatically from GitHub)
```

### 4️⃣ Create Worker Service
```
New Service → GitHub Repo → Select SAME repo
Name: radar-worker
Custom Start Command:
  celery -A app.extensions.celery worker --loglevel=info
```

### 5️⃣ Create Beat Service
```
New Service → GitHub Repo → Select SAME repo
Name: radar-beat
Custom Start Command:
  celery -A app.extensions.celery beat --loglevel=info
```

### 6️⃣ Set Environment Variables on ALL 3 Services

**Copy this template to each service (Variables → Raw Editor):**

```bash
# Auto-provided by Railway
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/1
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/2

# From generate_railway_keys.py
SECRET_KEY=PASTE_YOUR_GENERATED_KEY
JWT_SECRET_KEY=PASTE_YOUR_GENERATED_KEY
ENCRYPTION_KEY=PASTE_YOUR_GENERATED_KEY

# Application config
FLASK_ENV=production
FLASK_APP=app
ALLOWED_ORIGINS=https://radar-web.railway.app

# Add your API keys below (optional)
# ALPHA_VANTAGE_API_KEY=...
# CRUNCHBASE_API_KEY=...
# etc.
```

## ✅ Verification

### Check Service Status
```
All 5 services should show "Active" (green)
- Postgres ✓
- Redis ✓  
- radar-web ✓
- radar-worker ✓
- radar-beat ✓
```

### View Logs
```
Click service → Deployments → View logs
```

### Test Application
```
1. Open radar-web URL
2. Try to access the API
3. Check background tasks work
```

## 🔧 Common Commands

```bash
# Generate secure keys
python generate_railway_keys.py

# Verify setup before deploying
python verify_railway_setup.py

# View current directory structure
ls -la

# Check git status
git status

# Push changes
git add . && git commit -m "Update config" && git push
```

## 📊 Service Architecture

```
┌─────────────┐
│ PostgreSQL  │ ← Database (managed by Railway)
└─────────────┘
       ↑
       │
┌─────────────┐
│    Redis    │ ← Cache + Celery broker (managed)
└─────────────┘
       ↑
       │
┌─────────────┐
│  radar-web  │ ← Flask app (public URL)
└─────────────┘
       │
       ├─→ radar-worker (background tasks)
       │
       └─→ radar-beat (scheduled tasks)
```

## 🔑 Important Variables Reference

| Variable | Source | Required |
|----------|--------|----------|
| `DATABASE_URL` | Auto (Postgres) | ✓ |
| `REDIS_URL` | Auto (Redis) | ✓ |
| `SECRET_KEY` | generate_railway_keys.py | ✓ |
| `JWT_SECRET_KEY` | generate_railway_keys.py | ✓ |
| `ENCRYPTION_KEY` | generate_railway_keys.py | ✓ |
| `FLASK_ENV` | Set to "production" | ✓ |
| `ALLOWED_ORIGINS` | Your Railway domain | ✓ |
| API Keys | Your external services | Optional |

## ❗ Critical Reminders

1. **Same Keys on All Services**: Use IDENTICAL keys on web, worker, and beat
2. **Update ALLOWED_ORIGINS**: Replace with your actual Railway domain
3. **Volume for Storage**: Set up Railway Volume at `/app/storage` if needed
4. **OAuth Redirect**: Update OAuth redirect URI with Railway domain
5. **Monitor Costs**: Check Railway dashboard for usage

## 🆘 Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| Build fails | Check logs, verify requirements.txt |
| Can't connect to DB | Verify DATABASE_URL is set |
| Celery not working | Check Redis is running, verify env vars |
| 502 Bad Gateway | Check web service logs, verify PORT usage |
| CORS errors | Update ALLOWED_ORIGINS with correct domain |

## 📚 Documentation

- **Quick Start**: README_RAILWAY.md
- **Full Guide**: RAILWAY_DEPLOYMENT.md  
- **Env Template**: env.railway.example
- **This File**: QUICK_REFERENCE.md

## 🎉 Success Indicators

- ✓ All 5 services show "Active" status
- ✓ Web service has public URL accessible
- ✓ No errors in deployment logs
- ✓ Can login to application
- ✓ Background tasks process correctly

---

**Need more help?** See RAILWAY_DEPLOYMENT.md for detailed instructions.
