# 📁 GitHub Setup Guide

## Step 1: Create a New GitHub Repository

1. **Go to GitHub**: Open https://github.com in your browser
2. **Sign in** to your GitHub account (or create one if needed)
3. **Create New Repository**:
   - Click the "+" icon in the top right corner
   - Select "New repository"
   - Repository name: `global-markets-tracker` (or your preferred name)
   - Description: `Real-time global stock market tracker with YFinance backend`
   - Set to **Public** (required for free Railway deployment)
   - ✅ **Check "Add a README file"** 
   - ✅ **Add .gitignore**: Select "Python" template
   - License: Choose "MIT License" (recommended)
   - Click **"Create repository"**

## Step 2: Clone the Repository to Your Computer

```bash
# Replace YOUR_USERNAME with your GitHub username
git clone https://github.com/YOUR_USERNAME/global-markets-tracker.git
cd global-markets-tracker
```

## Step 3: Copy Your Project Files

Now you need to copy all your project files into the cloned repository folder. Here's your current project structure:

```
Your Project Files:
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Procfile
│   ├── runtime.txt
│   ├── .env.example
│   ├── README.md
│   └── test_api.py
├── css/
├── js/
├── .gitignore
├── index.html
├── global-markets-tracker.html
├── README.md
├── DEPLOYMENT.md
└── update_backend_url.py
```

### Copy Methods:

#### Option A: Manual Copy (Windows)
1. Open File Explorer to your project folder
2. Select ALL files and folders (Ctrl+A)
3. Copy them (Ctrl+C)
4. Navigate to the cloned `global-markets-tracker` folder
5. Paste everything (Ctrl+V)
6. **Replace the existing README.md** when prompted

#### Option B: Command Line (if you have Git installed)
```bash
# From your project directory, copy everything to the cloned repo
xcopy /E /I . "path\to\global-markets-tracker"
```

## Step 4: Add, Commit, and Push Your Code

```bash
# Navigate to your cloned repository
cd global-markets-tracker

# Add all files to git
git add .

# Commit your changes
git commit -m "Initial commit: Global Markets Tracker with YFinance backend"

# Push to GitHub
git push origin main
```

## Step 5: Verify Your Repository

1. Go back to your GitHub repository page
2. Refresh the page
3. You should see all your project files listed
4. Click through a few files to verify they uploaded correctly

## 🚀 You're Ready for Railway Deployment!

Once your code is on GitHub, you can proceed with Railway deployment:

1. **Go to Railway**: https://railway.app
2. **Sign up/Login** with your GitHub account
3. **Deploy from GitHub**: Select your `global-markets-tracker` repository
4. **Railway will automatically detect** your Python app from the `backend/` folder

## 📋 Next Steps After GitHub Setup

1. ✅ **Code on GitHub** (you'll complete this now)
2. 🚀 **Deploy backend to Railway** (follow DEPLOYMENT.md)
3. 🔗 **Update frontend URLs** (use update_backend_url.py)
4. 🌐 **Deploy frontend to Netlify**
5. 🧪 **Test end-to-end integration**

## Need Help?

- **Git not installed?** Download from: https://git-scm.com/download/win
- **GitHub Desktop** (easier GUI): https://desktop.github.com/
- **Questions?** The README.md and DEPLOYMENT.md files have detailed instructions

---

**Important**: Make sure your repository is **Public** for free Railway deployment. Private repositories require a paid Railway plan.