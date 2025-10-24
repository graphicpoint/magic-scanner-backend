# 🚀 MagicScanner - Complete Getting Started Guide

This guide will walk you through setting up the complete MagicScanner project from scratch to having it running on your phone!

## 📋 What You're Building

**MagicScanner** is a mobile app that uses computer vision to identify Magic: The Gathering cards from photos. Take a picture of multiple cards, and the app will tell you what they are, their value, and more!

**System Overview:**
```
Your Phone (iOS) → Backend API (Railway) → Scryfall API
     ↓                    ↓
  Camera Scan      Card Recognition
     ↓                    ↓
Display Results ← Identified Cards
```

## ✅ Prerequisites Checklist

Before starting, make sure you have:

- [ ] **Mac** with macOS (required for iOS development)
- [ ] **iPhone** for testing
- [ ] **Xcode** installed (from Mac App Store)
- [ ] **Node.js** 18+ installed ([nodejs.org](https://nodejs.org))
- [ ] **Python** 3.10+ installed
- [ ] **VS Code** installed ([code.visualstudio.com](https://code.visualstudio.com))
- [ ] **Git** installed
- [ ] **GitHub account** created
- [ ] **Railway account** created ([railway.app](https://railway.app))
- [ ] GitHub connected to Railway

## 🎯 Setup Overview

We'll do this in 4 phases:

1. **Phase 1**: Backend setup locally
2. **Phase 2**: Deploy backend to Railway  
3. **Phase 3**: Mobile app setup
4. **Phase 4**: Test on your phone

---

## 📦 Phase 1: Backend Setup (Local)

### Step 1.1: Clone Backend Repository

```bash
# Open Terminal

# Navigate to where you want the project
cd ~/Desktop

# Clone the backend
git clone https://github.com/graphicpoint/magic-scanner-backend.git
cd magic-scanner-backend
```

### Step 1.2: Create Python Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# You should see (venv) in your terminal now
```

### Step 1.3: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# This might take a few minutes...
```

### Step 1.4: Build Test Card Database

```bash
# Build a small test database (100 cards, ~5 minutes)
python build_card_database.py --test

# You'll see progress bars as it downloads and processes cards
# Wait for "Database build complete!"
```

### Step 1.5: Test Backend Locally

```bash
# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test it:**
- Open browser to: http://localhost:8000
- You should see: `{"status": "online", ...}`
- Open: http://localhost:8000/docs for API documentation

**Keep this terminal running!** Open a new one for next steps.

---

## 🚂 Phase 2: Deploy Backend to Railway

### Step 2.1: Push to GitHub

```bash
# In a NEW terminal (keep backend running in first)
cd ~/Desktop/magic-scanner-backend

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub.com named "magic-scanner-backend"
# Then connect and push:
git remote add origin https://github.com/graphicpoint/magic-scanner-backend.git
git branch -M main
git push -u origin main
```

### Step 2.2: Deploy to Railway

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose `magic-scanner-backend`
5. Railway will automatically:
   - Detect it's a Python project
   - Install dependencies
   - Start the server

### Step 2.3: Get Your Railway URL

1. In Railway dashboard, click your project
2. Go to **Settings** tab
3. Scroll to **Networking**
4. Click **"Generate Domain"**
5. Copy your URL: `https://magic-scanner-backend-production.up.railway.app`

### Step 2.4: Build Database on Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
cd ~/Desktop/magic-scanner-backend
railway link

# Build test database on Railway
railway run python build_card_database.py --test

# This will take ~5 minutes
# Database will be saved in Railway's file system
```

### Step 2.5: Test Railway Deployment

Open in browser:
```
https://your-railway-url.up.railway.app/health
```

Should see:
```json
{
  "status": "healthy",
  "database_loaded": true,
  "cards_in_database": 100
}
```

✅ **Backend is now deployed and ready!**

---

## 📱 Phase 3: Mobile App Setup

### Step 3.1: Clone Mobile App Repository

```bash
# In terminal
cd ~/Desktop

# Clone the app
git clone https://github.com/graphicpoint/magic-scanner-app.git
cd magic-scanner-app
```

### Step 3.2: Install Dependencies

```bash
# Install Node packages
npm install

# This might take a few minutes...
```

### Step 3.3: Configure API URL

**Find Your Local IP:**

```bash
# Run this command
ipconfig getifaddr en0

# Example output: 192.168.1.5
```

**Update API Config:**

Open `services/api.js` in VS Code and update:

```javascript
const API_CONFIG = {
  LOCAL_URL: 'http://192.168.1.5:8000', // YOUR IP HERE!
  PRODUCTION_URL: 'https://your-railway-url.up.railway.app', // YOUR RAILWAY URL!
  USE_LOCAL: true, // true = local, false = Railway
};
```

**Important:** 
- Use your **actual** local IP (not 127.0.0.1)
- Phone and computer must be on **same WiFi**

### Step 3.4: Start Expo Development Server

```bash
# Start the app
npm start

# Or if that doesn't work:
npx expo start
```

You should see:
```
› Metro waiting on exp://192.168.1.5:8081
› Scan the QR code above with Expo Go (Android) or Camera app (iOS)

████████████████████
████████████████████  ← QR CODE
████████████████████
```

---

## 📲 Phase 4: Run on Your iPhone

### Step 4.1: Install Expo Go

1. Open **App Store** on your iPhone
2. Search for **"Expo Go"**
3. Install it

### Step 4.2: Scan QR Code

1. Open **Camera app** on iPhone
2. Point at QR code in terminal
3. Tap notification that appears
4. App opens in Expo Go!

### Step 4.3: Grant Permissions

When the app starts:
1. Tap **"Scan Cards"**
2. Allow **Camera** access when prompted
3. Allow **Photos** access when prompted

### Step 4.4: Test Scanning!

1. Lay out some Magic cards on a table
2. Tap the **camera button** in the app
3. Point camera at cards
4. Tap **capture button**
5. Wait for processing...
6. See your cards identified! 🎉

---

## 🧪 Testing Checklist

Go through this checklist:

**Backend Tests:**
- [ ] Local backend responds at http://localhost:8000
- [ ] Railway backend responds at your Railway URL
- [ ] `/health` endpoint shows database_loaded: true
- [ ] API docs visible at /docs

**Mobile App Tests:**
- [ ] App launches in Expo Go
- [ ] Home screen displays correctly
- [ ] Can navigate to Camera screen
- [ ] Camera view shows
- [ ] Can take photo
- [ ] Processing indicator shows
- [ ] Results display with card images
- [ ] Prices show correctly
- [ ] Can navigate back to home

---

## 🐛 Common Issues & Solutions

### Issue: "Cannot connect to backend"

**Check:**
1. Is backend running? (terminal should show uvicorn)
2. Is API URL correct in `services/api.js`?
3. Are phone and computer on same WiFi?
4. Can you open http://YOUR_IP:8000/health in Safari on your phone?

**Solution:**
```bash
# Find your IP again
ipconfig getifaddr en0

# Update services/api.js with correct IP
# Restart expo: Press 'r' in terminal
```

### Issue: "No cards detected"

**Reasons:**
- Cards too small in frame
- Poor lighting
- Cards overlapping
- Image too blurry

**Solutions:**
- Take photo from directly above
- Use good lighting
- Keep cards separated
- Hold phone steady

### Issue: "Database not loaded"

**Solution:**
```bash
# Build database again
cd magic-scanner-backend
source venv/bin/activate
python build_card_database.py --test
```

### Issue: Camera not working in Expo Go

**Solution:**
Use development build instead:
```bash
cd magic-scanner-app
npx expo run:ios
```

This requires Xcode and will build a real iOS app on your phone.

---

## 🎉 You're Done!

You now have:
- ✅ Backend API running on Railway
- ✅ Mobile app on your phone
- ✅ Full card scanning functionality

### 🎯 Next Steps

**For Development:**
1. Open backend in VS Code
2. Open mobile app in VS Code
3. Make changes → See them update live!

**Switch to Railway Backend:**
```javascript
// In services/api.js
USE_LOCAL: false  // Now uses Railway!
```

**Build Full Database:**
```bash
railway run python build_card_database.py
# This takes 3-4 hours but scans ALL Magic cards!
```

---

## 📚 Additional Resources

### Documentation
- Backend: See `/magic-scanner-backend/README.md`
- Mobile: See `/magic-scanner-app/README.md`
- API: http://your-railway-url.up.railway.app/docs

### Useful Commands

**Backend:**
```bash
# Start local server
uvicorn main:app --reload

# Build database
python build_card_database.py --test

# Check database
python -c "from card_matching import load_card_database; print(len(load_card_database()), 'cards')"
```

**Mobile App:**
```bash
# Start dev server
npm start

# Run on iOS
npx expo run:ios

# Clear cache
npx expo start -c
```

**Railway:**
```bash
# View logs
railway logs

# Run command
railway run python script.py

# Open dashboard
railway open
```

---

## 🎓 Understanding the Architecture

### How It Works:

```
1. 📱 You take photo of cards
   ↓
2. 📤 App uploads image to backend
   ↓
3. 🔍 Backend uses OpenCV to detect individual cards
   ↓
4. 🏷️ Creates perceptual hash for each card
   ↓
5. 🔎 Matches against database of 20,000+ card hashes
   ↓
6. 🌐 Fetches details from Scryfall API
   ↓
7. 📥 Returns results to app
   ↓
8. ✨ You see your cards identified!
```

### Key Technologies:

- **React Native + Expo**: Mobile app framework
- **FastAPI**: Python web framework
- **OpenCV**: Computer vision for card detection
- **ImageHash**: Perceptual hashing for matching
- **Scryfall API**: Card database
- **Railway**: Cloud hosting

---

## 💡 Tips for Development

1. **Hot Reload**: Changes to code reload automatically!
2. **Console Logs**: Check terminal for debug output
3. **Test Locally First**: Faster development cycle
4. **Use Railway for Production**: Share with friends!

---

## 📧 Need Help?

- Check READMEs in each project folder
- Open GitHub issue
- Review troubleshooting sections above

---

## 🎊 Congratulations!

You've successfully built and deployed a complete computer vision application! 

**What you learned:**
- Python backend development
- React Native mobile apps
- Computer vision concepts
- API integration
- Cloud deployment
- Full-stack development

Keep building and have fun scanning cards! 🎴✨

---

**Made by graphicpoint • Powered by Scryfall • Built with ❤️**
