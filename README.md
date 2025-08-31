# Global Markets Tracker - Live Data

A professional real-time stock market tracker that displays live data for 15 major global market indices. Features interactive charts, candlestick analysis, and real-time data from YFinance API via Railway backend.

## 🚀 **Live Data Only - No Demo Mode**

This tracker connects directly to live market data. All data is real-time from global stock exchanges via our Python Flask backend on Railway.

## 🌐 **Live Deployment**

- **Backend API**: https://global-indices-tracker-production.up.railway.app
- **Frontend**: Deploy `global-markets-tracker.html` to Netlify or any static hosting platform

## 📁 **Main Files**

- **`global-markets-tracker.html`** - 🎯 **Main live-only tracker** (single file, ready for deployment)
- **`global-markets-tracker-clean.html`** - Clean backup version
- **`backend/`** - Python Flask API with YFinance integration (deployed on Railway)
- **`index.html`** - Original modular version

## ✨ **Features Completed**
- **Single 24-hour period view** with date picker (no multi-day ranges)
- **Australian time display**: X-axis shows Australian local time (00:00 = midnight Sydney)
- **Complete Australian market coverage**: All major ASX indices included:
  - **ASX 200** - Top 200 companies by market cap
  - **ASX 300** - Extended market coverage (top 300)
  - **ASX 50** - Blue chip large caps
  - **ASX 100** - Mid-tier large companies  
  - **ASX Small Cap** - Small cap index
- **Index selection controls**: Checkboxes to choose which indices to display
- **Quick selection buttons**: Select All, None, and By Region (Oceania/Asia/Europe/Americas)
- **Market-specific data display**: Indices only show data during their actual market hours
- Performance comparison showing percentage change from market open for each active index
- Adjustable time interval from 5 minutes to 1 hour for intraday data
- Candlestick (OHLC) view for individual indices during their market hours only
- **24-hour Australian time scale on X-axis** with HH:MM format display (00:00 = midnight Sydney)
- **Market hours visualization** showing when each market is open/closed in Australian local time
- Market hours indicator toggle checkbox
- Color-coded legend showing only active/selected markets for the selected date
- **ASX 200 default selection** for Australian users
- Zoom and pan (mouse wheel, drag) with data zoom controls
- Demo data generator creating realistic market-hour-specific data
- YFinance integration placeholder (requires backend implementation)
- Responsive UI built with Tailwind CSS and ECharts

## How It Works
- index.html: UI layout and controls with market hours toggle
- css/style.css: Color palette and minor styles
- js/providers.js: Data provider module with demo YFinance-style generator and YFinance integration placeholder
- js/main.js: UI logic, chart rendering (ECharts), 24-hour time display, market hours visualization
- global-markets-tracker.html: Single-file version with all code embedded

## Usage
1. Open index.html or global-markets-tracker.html in a modern browser on Windows 11 or any OS.
2. **Select a specific date** using the date picker (defaults to today).
3. **Choose indices to display** using checkboxes in the sidebar:
   - **Australian indices**: ASX 200, ASX 300, ASX 50, ASX 100, ASX Small Cap
   - Individual checkboxes for each index (15 total indices)
   - "Select All" button to enable all indices
   - "None" button to clear all selections
   - "By Region" button to cycle through Oceania/Asia/Europe/Americas
4. Select View: Performance (Line) to compare selected indices, or Candlestick (Single Index) for OHLC.
5. Choose Interval (5m to 1h for intraday data).
6. Toggle "Show Market Hours" to display market names and timing.
7. **Only selected markets that were open on the selected date will show data**.
8. **X-axis displays 24-hour Australian time format (HH:MM)** - 00:00 = midnight Sydney time!
9. **Market hours are shown in Australian local time** - intuitive for Australian traders
10. For live data: choose Data = YFinance (requires backend setup), otherwise use Demo mode.

## Entry URIs
- /index.html
  - Query params: none. All configuration is client-side via UI controls.

## Backend API Now Available! 🎉
- **✅ YFinance Python Backend**: Complete Flask API with real market data
- **✅ Railway/Render Deployment**: Free hosting options with auto-deployment
- **✅ Live Data Integration**: Frontend connects to real YFinance data
- **✅ Error Handling**: Graceful fallback to demo data if API unavailable
- **✅ Australian Market Priority**: All ASX indices supported with live data

## Not Yet Implemented
- Real-time market status indicators (pre-market, market open, after-hours, closed)
- Persistent user settings across sessions
- Advanced market hours overlays (lunch breaks, half days, holidays)
- Redis caching for API performance optimization

## Recommended Next Steps
- **🚀 Deploy the backend**: Follow `DEPLOYMENT.md` to get live YFinance data
- **📊 Add technical indicators**: Moving averages, RSI, MACD in candlestick view
- **💾 Add localStorage**: Remember user settings and selected indices
- **⏰ Real-time status**: Show market open/closed/pre-market status
- **📅 Market holidays**: Detect and display market closures
- **⚡ Performance optimization**: Add Redis caching to backend API
- **🔔 Price alerts**: Notify when indices hit certain levels

## Project Name, Goals, Main Features
- Name: Global Markets Tracker
- Goal: Provide an easy, responsive way to visualize global stock indices across time scales (5 minutes to 2 years) with performance and candlestick views.
- Main features: Multi-index performance comparison; single-index candlesticks; adjustable intervals and ranges; color-coded labels; zoom/pan.

## Public URLs
- This is a static project. No default public URL in the dev environment.
- When published, index.html will be the primary entry point.

## Data Models and Storage
- No backend storage used. Data fetched live from APIs or generated locally.
- For the platform's built-in Tables API, not used in this project.

## Deployment
To deploy your website and make it live, please go to the Publish tab where you can publish your project with one click. The Publish tab will handle all deployment processes automatically and provide you with the live website URL.
