# MagicScanner Mobile App

React Native + Expo mobile application for scanning and identifying Magic: The Gathering cards using your phone's camera.

## 📱 Features

- **Camera Scanning**: Take photos of multiple cards at once
- **Card Recognition**: Identify cards using backend computer vision
- **Card Details**: View card information, set, rarity, and current prices
- **Modern UI**: Beautiful dark-themed interface optimized for mobile
- **Cross-Platform**: Works on both iOS and Android

## 🎯 Prerequisites

- **Node.js** 18 or higher
- **npm** or **yarn**
- **Expo Go app** on your iPhone (from App Store)
- **Backend API** running (see backend README)

## 🚀 Quick Start

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/graphicpoint/magic-scanner-app.git
cd magic-scanner-app

# Install dependencies
npm install
```

### 2. Configure API URL

**IMPORTANT**: Update the API URL in `services/api.js`

**For Local Development:**

Find your computer's local IP address:

```bash
# Mac/Linux
ipconfig getifaddr en0

# Or check System Preferences > Network
```

Then update `services/api.js`:

```javascript
const API_CONFIG = {
  LOCAL_URL: 'http://YOUR_LOCAL_IP:8000', // e.g., http://192.168.1.5:8000
  PRODUCTION_URL: 'https://your-railway-app.up.railway.app',
  USE_LOCAL: true, // true for development, false for production
};
```

**Why not localhost?**
- `localhost` or `127.0.0.1` refers to the phone itself, not your computer
- You need to use your computer's network IP address
- Make sure your phone and computer are on the same WiFi network

**For Production:**
- Deploy backend to Railway
- Update `PRODUCTION_URL` with your Railway URL
- Set `USE_LOCAL: false`

### 3. Start the App

```bash
npm start
```

This will:
1. Start the Expo development server
2. Show a QR code in your terminal
3. Give you a URL to open in browser

### 4. Run on Your Phone

**Option A: Expo Go (Easiest for Development)**

1. Install **Expo Go** from App Store
2. Scan the QR code with your iPhone camera
3. App will open in Expo Go
4. Changes to code will reload automatically! 🔥

**Option B: Development Build (For Full Camera Access)**

If Expo Go has camera limitations:

```bash
# Build and run on connected iPhone
npx expo run:ios

# Or for Android
npx expo run:android
```

This requires:
- Xcode installed (for iOS)
- iPhone connected via USB
- Developer account configured in Xcode

## 📁 Project Structure

```
magic-scanner-app/
├── App.js                    # Main app component with navigation
├── app.json                  # Expo configuration
├── package.json              # Dependencies
│
├── screens/
│   ├── HomeScreen.js        # Home page with main actions
│   ├── CameraScreen.js      # Camera interface for scanning
│   ├── ScanResultsScreen.js # Display scan results
│   └── CollectionScreen.js  # Collection management (coming soon)
│
├── services/
│   └── api.js               # Backend API communication
│
└── assets/
    ├── icon.png             # App icon
    ├── splash.png           # Splash screen
    └── adaptive-icon.png    # Android adaptive icon
```

## 🎨 Screens

### Home Screen
- Main landing page
- Quick access to scan and collection
- Info and instructions

### Camera Screen
- Live camera view with guidelines
- Capture button to take photo
- Photo library access
- Real-time processing feedback

### Scan Results Screen
- Display all detected cards
- Card images from Scryfall
- Prices and details
- Select cards to add to collection
- Links to Scryfall for more info

### Collection Screen
- View saved cards (coming soon)
- Search and filter
- Statistics and value tracking

## 🔧 Development Tips

### Hot Reload

When using Expo Go or development build, changes to your code will automatically reload the app:
- Save file in VS Code → App reloads
- No need to rebuild or restart!

### Debug Console

View console logs in terminal where you ran `npm start`:
```
Console logs will appear here...
```

### Network Issues?

If the app can't connect to the backend:

1. **Check Backend is Running**
```bash
# In backend directory
uvicorn main:app --reload
# Should see: Uvicorn running on http://0.0.0.0:8000
```

2. **Verify API URL**
```javascript
// In services/api.js
console.log('API URL:', getApiUrl());
// Should match your backend URL
```

3. **Test Connection**
```bash
# From your phone's browser, try to access:
http://YOUR_LOCAL_IP:8000/health

# Should return JSON: {"status": "healthy", ...}
```

4. **Check WiFi**
- Phone and computer on same network?
- Corporate/school WiFi may block connections
- Try personal hotspot if needed

### Camera Not Working?

**In Expo Go:**
- Camera API is limited in Expo Go
- Use development build instead: `npx expo run:ios`

**Permissions:**
- App will request camera permission on first launch
- If denied, go to Settings > MagicScanner > Camera

## 📦 Building for Production

### iOS (TestFlight/App Store)

1. **Install EAS CLI**
```bash
npm install -g eas-cli
eas login
```

2. **Configure Project**
```bash
eas build:configure
```

3. **Build**
```bash
# Build for TestFlight
eas build --platform ios --profile production

# Submit to App Store
eas submit --platform ios
```

### Android (Google Play)

```bash
# Build AAB for Google Play
eas build --platform android --profile production

# Submit to Google Play
eas submit --platform android
```

## 🧪 Testing

### Manual Testing Checklist

- [ ] App launches successfully
- [ ] Camera opens and shows live view
- [ ] Can take photo
- [ ] Can select image from library
- [ ] Processing indicator shows
- [ ] Results display correctly
- [ ] Card images load
- [ ] Prices display
- [ ] Can navigate back
- [ ] Can view collection screen

### Test with Sample Images

1. Download Magic card images from Scryfall
2. Save to your phone's camera roll
3. Use "Photo Library" button in camera screen
4. Select test image

## 🐛 Troubleshooting

### "Network request failed"

**Problem:** App can't connect to backend

**Solutions:**
1. Check `services/api.js` has correct URL
2. Verify backend is running: `http://YOUR_IP:8000/health`
3. Ensure phone and computer on same WiFi
4. Try using phone's hotspot

### "No cards detected"

**Problem:** Backend can't find cards in image

**Solutions:**
1. Ensure good lighting
2. Cards should be flat and clearly visible
3. Don't overlap cards
4. Take photo from directly above

### "Card database not loaded"

**Problem:** Backend hasn't built card database

**Solution:**
```bash
# In backend directory
python build_card_database.py --test
```

### App Crashes on Camera

**Problem:** Expo Go camera limitations

**Solution:**
Build development version:
```bash
npx expo run:ios
```

### "Module not found"

**Problem:** Missing dependencies

**Solution:**
```bash
rm -rf node_modules
npm install
```

## 🔐 Permissions

The app requires these permissions:

- **Camera**: To take photos of cards
- **Photo Library**: To select existing images

Permissions are requested on first use of each feature.

## 🎨 Customization

### Change Colors

Edit theme colors in screen files:

```javascript
const styles = StyleSheet.create({
  primaryColor: '#ff6b6b',    // Main accent color
  secondaryColor: '#4ecdc4',   // Secondary accent
  backgroundColor: '#0f0f1e',  // Dark background
  // ...
});
```

### Change API Endpoint

Update `services/api.js`:

```javascript
const API_CONFIG = {
  LOCAL_URL: 'http://your-ip:8000',
  PRODUCTION_URL: 'https://your-railway-app.up.railway.app',
  USE_LOCAL: true,
};
```

## 📊 Performance

- **App Size**: ~20-30 MB
- **Scan Time**: 2-5 seconds (depends on backend)
- **Memory Usage**: ~100-150 MB
- **Battery**: Moderate drain during scanning

## 🚀 Next Features

- [ ] Collection storage with Supabase
- [ ] Deck builder
- [ ] Price tracking
- [ ] Export to CSV
- [ ] Card trade lists
- [ ] Wishlist management

## 📝 Notes

### Expo Go vs Development Build

| Feature | Expo Go | Dev Build |
|---------|---------|-----------|
| Setup | Quick | Requires Xcode |
| Camera | Limited | Full access |
| Hot Reload | ✅ Yes | ✅ Yes |
| Native Modules | ❌ Limited | ✅ Full |
| Best For | Quick testing | Full development |

### iOS vs Android

The app is designed to work on both platforms, but is currently optimized for iOS. Android support is complete but may have minor UI differences.

## 🤝 Contributing

Want to add features?

1. Fork the repo
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📧 Support

Issues or questions? Open a GitHub issue!

## 🙏 Credits

- [Expo](https://expo.dev) - React Native framework
- [React Navigation](https://reactnavigation.org) - Navigation
- [Expo Camera](https://docs.expo.dev/versions/latest/sdk/camera/) - Camera API
- Backend powered by FastAPI + OpenCV

---

Built with ❤️ for Magic: The Gathering players

**Happy Scanning!** 🎴✨
