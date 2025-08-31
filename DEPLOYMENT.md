# 🚀 Global Markets Tracker - Deployment Guide

Complete guide to deploy your stock market tracker with real YFinance data.

## 📋 Overview

Your tracker now has two parts:
1. **Frontend**: HTML/CSS/JS files (static website)
2. **Backend**: Python Flask API (provides real YFinance data)

## 🖥️ Backend Deployment (Python API)

### Option 1: Railway (Recommended - Free Tier)

Railway offers generous free tier perfect for this API.

#### Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Backend**
   ```bash
   # Fork this repository or push to your GitHub
   git add backend/
   git commit -m "Add YFinance backend"
   git push origin main
   ```

3. **Connect to Railway**
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Choose "Deploy from repo"
   - Set **Root Directory**: `backend`

4. **Railway Auto-Deployment**
   - Railway detects `requirements.txt` and `Procfile`
   - Automatically installs Python 3.11
   - Runs: `pip install -r requirements.txt`
   - Starts: `gunicorn app:app`

5. **Get Your API URL**
   - Railway provides: `https://your-app-name.railway.app`
   - Test: `https://your-app-name.railway.app/api/health`

#### Railway Environment Variables (Optional):
```bash
FLASK_ENV=production
FLASK_DEBUG=False
```

### Option 2: Render (Free Tier)

1. **Connect GitHub**
   - Go to [render.com](https://render.com)
   - Connect your GitHub account

2. **Create Web Service**
   - Click "New" → "Web Service"
   - Select your repository
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Python Version**: 3.11.6

3. **Deploy**
   - Render builds and deploys automatically
   - Get URL: `https://your-app-name.onrender.com`

### Option 3: Heroku (Paid)

```bash
# Install Heroku CLI
heroku create your-markets-api

# Deploy backend subfolder
git subtree push --prefix backend heroku main

# Get URL
heroku info
```

### Option 4: Local Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```
API available at: `http://localhost:5000`

## 🌐 Frontend Deployment

### Update Backend URL

First, update your frontend with the deployed backend URL:

```javascript
// In global-markets-tracker.html and js/providers.js
// Replace this line:
: 'https://your-backend-url.railway.app';  // Production - UPDATE THIS!

// With your actual Railway URL:
: 'https://markets-tracker-backend.railway.app';
```

### Option 1: Netlify (Recommended for Frontend)

1. **Drag & Drop Deploy**
   - Go to [netlify.com](https://netlify.com)
   - Drag your project folder to deploy area
   - Get URL: `https://random-name.netlify.app`

2. **GitHub Integration**
   - Connect GitHub repository
   - Auto-deploy on push
   - Custom domain support

### Option 2: Vercel

1. **GitHub Deploy**
   - Go to [vercel.com](https://vercel.com)
   - Import GitHub repository
   - Auto-deploy

### Option 3: GitHub Pages

```bash
# Enable GitHub Pages in repository settings
# Choose source: GitHub Actions

# Create .github/workflows/deploy.yml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./
```

## 🔧 Configuration

### Backend URL Configuration

Update these files with your deployed backend URL:

1. **global-markets-tracker.html** (line ~132):
```javascript
const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000'
  : 'https://YOUR-ACTUAL-BACKEND-URL.railway.app';  // UPDATE THIS!
```

2. **js/providers.js** (line ~97):
```javascript
const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000'
  : 'https://YOUR-ACTUAL-BACKEND-URL.railway.app';  // UPDATE THIS!
```

### CORS Configuration

If you get CORS errors, update backend `app.py`:

```python
# Add your frontend domain
CORS(app, origins=[
    "http://localhost:3000",
    "https://your-frontend-domain.netlify.app",
    "https://your-custom-domain.com"
])
```

## 🧪 Testing Your Deployment

### Test Backend API

```bash
# Health check
curl https://your-backend-url.railway.app/api/health

# Get ASX 200 data
curl "https://your-backend-url.railway.app/api/stock/^AXJO?interval=5m&date=2024-01-15"

# List all symbols
curl https://your-backend-url.railway.app/api/symbols
```

### Test Frontend

1. **Open your deployed frontend URL**
2. **Select "YFinance (live data)" from dropdown**
3. **Watch for status indicator**:
   - 🟡 Fetching... (loading)
   - 🟢 Live Data (success)
   - 🔴 API Error (fallback to demo)

## 🚨 Troubleshooting

### Common Issues

#### 1. CORS Errors
```
Access to fetch at 'your-backend-url' has been blocked by CORS policy
```
**Solution**: Add your frontend domain to CORS origins in `app.py`

#### 2. YFinance Rate Limits
```
HTTP 429: Too Many Requests
```
**Solution**: YFinance has ~200 requests/hour limit. Use demo mode or implement caching.

#### 3. Symbol Not Found
```
No data found for symbol
```
**Solution**: Some symbols may not be available in YFinance. Check symbol format.

#### 4. Backend Not Responding
```
Failed to fetch
```
**Solution**: Check if backend is deployed and accessible at the URL.

### Debug Steps

1. **Check backend health**: `https://your-backend-url/api/health`
2. **Check browser console** for error messages
3. **Check network tab** for failed requests
4. **Verify backend URL** in frontend code

## 📊 Performance Optimization

### Backend Optimizations

1. **Add Redis Caching**:
```python
import redis
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=300)  # 5 minute cache
def get_market_data(symbol, interval, date):
    # ... existing code
```

2. **Rate Limiting**:
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)
```

### Frontend Optimizations

1. **Batch Requests**: Use `/api/bulk` endpoint
2. **Local Caching**: Store data in localStorage
3. **Debounce**: Limit rapid API calls

## 🎯 Production Checklist

- [ ] Backend deployed to Railway/Render
- [ ] Frontend deployed to Netlify/Vercel
- [ ] Backend URL updated in frontend code
- [ ] CORS configured for frontend domain
- [ ] API health check working
- [ ] YFinance data loading successfully  
- [ ] Error handling working (fallback to demo)
- [ ] Status indicator showing correct state
- [ ] All Australian indices working
- [ ] Custom domain configured (optional)

## 🔗 Final URLs

After deployment, you'll have:
- **Frontend**: `https://your-app.netlify.app`
- **Backend API**: `https://your-backend.railway.app`
- **API Docs**: `https://your-backend.railway.app/api/symbols`

Your Global Markets Tracker is now live with real YFinance data! 🎉