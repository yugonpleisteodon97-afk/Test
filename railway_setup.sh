#!/bin/bash
# Railway Setup Script
# This script helps you set up your Railway project

echo "🚂 Railway Setup for Radar Application"
echo "======================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git repository not initialized"
    echo "Please run: git init"
    exit 1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Railway CLI not found. Installing..."
    
    # Install for different platforms
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        # Linux or macOS
        bash <(curl -fsSL https://railway.app/install.sh)
    else
        echo "⚠️  Please install Railway CLI manually:"
        echo "   npm i -g @railway/cli"
        echo "   or visit: https://docs.railway.app/develop/cli"
        exit 1
    fi
fi

echo "✅ Railway CLI is installed"
echo ""

# Login to Railway
echo "🔐 Logging into Railway..."
echo "Your API Token: 4e056c91-6301-425b-a231-ca29c5a725cf"
echo ""

# Set the Railway API token
export RAILWAY_TOKEN=4e056c91-6301-425b-a231-ca29c5a725cf

# Initialize Railway project
echo "📝 Initializing Railway project..."
railway init

echo ""
echo "✅ Railway project initialized!"
echo ""

# Create services
echo "📋 Next steps:"
echo ""
echo "1. Add PostgreSQL Database:"
echo "   Go to Railway Dashboard → New Service → Database → PostgreSQL"
echo ""
echo "2. Add Redis:"
echo "   Go to Railway Dashboard → New Service → Database → Redis"
echo ""
echo "3. Deploy Web Service:"
echo "   railway up --service radar-web"
echo ""
echo "4. Create Celery Worker Service:"
echo "   Go to Railway Dashboard → New Service → GitHub Repo → Select same repo"
echo "   Set start command: celery -A app.extensions.celery worker --loglevel=info"
echo ""
echo "5. Create Celery Beat Service:"
echo "   Go to Railway Dashboard → New Service → GitHub Repo → Select same repo"
echo "   Set start command: celery -A app.extensions.celery beat --loglevel=info"
echo ""
echo "6. Configure environment variables using env.railway.example as reference"
echo ""
echo "📖 For detailed instructions, see RAILWAY_DEPLOYMENT.md"
echo ""
echo "🚀 Happy deploying!"
