# Macro-Event-Sentiment-Pipeline
A full-stack financial intelligence platform predicting NIFTY 50 market movements using FinBERT sentiment analysis, real-time news aggregation, and yfinance. Built with FastAPI and Next.js.
# 📊 Macro-Event Sentiment Pipeline

![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-success)
![Python](https://img.shields.io/badge/Python-3.8%2+-%2314354C.svg?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-13+-black?logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)

A full-stack financial intelligence platform engineered to provide real-time market sentiment analysis and NIFTY 50 predictions. This system ingests live market data and breaking financial news, processing them through a deterministic sentiment engine to output a highly stable, impact-weighted "Market Thermometer."

## ✨ Key Features

* **Real-Time Market Tracking:** Fetches live OHLCV data for the NIFTY 50 via the `yfinance` API with auto-polling every 60 seconds.
* **Deterministic Sentiment Analysis:** Utilizes a custom keyword-based engine (and **FinBERT**) to ensure 100% consistent scoring across refreshes, eliminating prediction volatility.
* **Smart News Aggregation:** Scrapes Google News RSS feeds, strictly filtering for finance-only content (95%+ relevance) and validating article freshness (< 6 hours).
* **Impact-Weighted Aggregation:** Calculates a comprehensive Bull/Bear ratio and a 0-100° market temperature based on news severity and freshness.
* **Graceful Degradation:** Employs a smart 2h → 6h fallback strategy during slow news cycles to ensure the dashboard remains functional and informative.

## 🛠️ Technology Stack

**Backend:**
* **Framework:** FastAPI (Python)
* **Data Sources:** `yfinance` API, Google News RSS (`feedparser`)
* **Core Libraries:** `pandas`, `hashlib`, Transformers (FinBERT)

**Frontend:**
* **Framework:** Next.js 13 (React / TypeScript)
* **Visualization:** Recharts
* **Styling:** Tailwind CSS

## 🏗️ Architecture Overview

The pipeline operates on a decoupled client-server architecture:

1.  **Next.js Client:** Auto-polls the backend every 60s/5min, rendering the Market Thermometer, real-time Recharts stock graphs, and the recent headline sidebar.
2.  **FastAPI Server:** Exposes 4 RESTful endpoints (`/predict-window`, `/stock-data`, `/live-news`). It handles all data scraping, freshness validation, financial keyword filtering, and sentiment computation before serving the normalized JSON payloads to the frontend.

## 🚀 Quick Start

### Prerequisites
* Python 3.8+
* Node.js 16+
* npm or yarn

### 1. Backend Setup
```bash
# Clone the repository
git clone [https://github.com/yourusername/macro-sentiment-pipeline.git](https://github.com/yourusername/macro-sentiment-pipeline.git)
cd macro-sentiment-pipeline/backend

# Install dependencies
pip install -r requirements.txt
# OR run the provided batch script: install_dependencies.bat

# Start the FastAPI server
python main.py
# The API will be live at: [http://127.0.0.1:8000](http://127.0.0.1:8000)
```

2. Frontend Setup
# Navigate to the frontend directory
cd ../sentiment-frontend

# Install Node modules
``` bash
npm install

# Start the Next.js development server
npm run dev
# The dashboard will be live at: http://localhost:3000
```
🧠 Evolution: MVP to Production
This project underwent 5 major iterations to transition from a conceptual prototype to a production-grade tool:

Mock → Real Data: Integrated live yfinance tracking.

Random → Deterministic: Replaced unstable heuristics with strict FinBERT/keyword-based sentiment anchoring.

Generic → Finance-Only: Implemented strict 40+ keyword filters to achieve 95% domain relevance.

Stale → Fresh: Enforced strict programmatic < 6 hours time windows.

Fragile → Resilient: Built tiered fallback states to prevent UI collapse during missing data states.

👤 Author
Developed and maintained by a Data Science & AI student at IIT Guwahati. Open to collaborations on quantitative analysis, machine learning integrations, and FinTech system design.
