import uvicorn
import feedparser 
import random
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from email.utils import parsedate_to_datetime
import time
import hashlib

app = FastAPI(title="Macro-Event Sentiment API")

# Allow Next.js to talk to Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewsInput(BaseModel):
    sentiment_score: float
    impact_numeric: int
    sector_tech: int

@app.get("/")
def read_root():
    return {"status": "API is live!"}

# Deterministic sentiment analyzer (replaces random sentiment)
def analyze_sentiment(headline: str) -> float:
    """
    Generate deterministic sentiment score based on headline text.
    Same headline always produces same sentiment score.
    
    Uses keyword-based heuristics + text hashing for consistency.
    
    Returns:
        Sentiment score between -1.0 (bearish) and +1.0 (bullish)
    """
    headline_lower = headline.lower()
    
    # Bullish keywords and their weights
    bullish_keywords = {
        'surge': 0.7, 'rally': 0.7, 'gain': 0.6, 'rise': 0.5, 'high': 0.5,
        'jump': 0.6, 'soar': 0.8, 'climb': 0.5, 'advance': 0.5, 'boost': 0.6,
        'up': 0.4, 'positive': 0.6, 'growth': 0.6, 'record': 0.7, 'milestone': 0.6,
        'profit': 0.5, 'strong': 0.5, 'bullish': 0.8, 'optimistic': 0.6,
        'buy': 0.5, 'buying': 0.5, 'outperform': 0.6, 'beat': 0.5, 'exceed': 0.6,
        'recovery': 0.6, 'expansion': 0.5, 'improve': 0.5, 'success': 0.6
    }
    
    # Bearish keywords and their weights
    bearish_keywords = {
        'fall': -0.6, 'drop': -0.6, 'decline': -0.6, 'plunge': -0.8, 'crash': -0.9,
        'down': -0.4, 'low': -0.5, 'slump': -0.7, 'tumble': -0.7, 'sink': -0.6,
        'negative': -0.6, 'loss': -0.6, 'weak': -0.5, 'bearish': -0.8, 'concern': -0.5,
        'worry': -0.5, 'risk': -0.4, 'fear': -0.6, 'sell': -0.5, 'selling': -0.5,
        'underperform': -0.6, 'miss': -0.5, 'disappoint': -0.6, 'crisis': -0.8,
        'recession': -0.8, 'inflation': -0.4, 'cut': -0.4, 'reduce': -0.4
    }
    
    # Calculate keyword-based sentiment
    sentiment_score = 0.0
    keyword_matches = 0
    
    for keyword, weight in bullish_keywords.items():
        if keyword in headline_lower:
            sentiment_score += weight
            keyword_matches += 1
    
    for keyword, weight in bearish_keywords.items():
        if keyword in headline_lower:
            sentiment_score += weight
            keyword_matches += 1
    
    # If keywords found, normalize by match count
    if keyword_matches > 0:
        sentiment_score = sentiment_score / keyword_matches
    else:
        # No keywords found - use deterministic hash-based approach
        # This ensures same headline always gets same sentiment
        headline_hash = int(hashlib.md5(headline.encode()).hexdigest(), 16)
        # Map hash to range [-0.3, 0.3] for neutral headlines
        sentiment_score = ((headline_hash % 1000) / 1000 - 0.5) * 0.6
    
    # Clamp to [-1.0, 1.0] range
    sentiment_score = max(-1.0, min(1.0, sentiment_score))
    
    return round(sentiment_score, 2)

# Helper function to validate article freshness
def is_article_fresh(entry, max_age_hours=24):
    """
    Check if an RSS entry was published within the last max_age_hours.
    
    Args:
        entry: RSS feed entry with published date
        max_age_hours: Maximum age in hours (default: 24)
    
    Returns:
        Boolean indicating if article is fresh
    """
    try:
        # Try to parse the published date
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            # Convert struct_time to datetime
            pub_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        elif hasattr(entry, 'published'):
            # Fallback: parse RFC 2822 date string
            pub_time = parsedate_to_datetime(entry.published)
            # Make timezone-naive for comparison
            pub_time = pub_time.replace(tzinfo=None)
        else:
            # No date information - reject to be safe
            return False
        
        # Calculate age
        now = datetime.now()
        age = now - pub_time
        
        # Return True if article is within max_age_hours
        return age.total_seconds() / 3600 <= max_age_hours
        
    except Exception as e:
        # If date parsing fails, reject the article
        return False

# --- THE MISSING ROUTE ---
@app.get("/live-news")
def get_live_news():
    """
    Fetch finance-focused news from the last 6 hours with strict date validation.
    """
    # Multiple finance-focused RSS feeds
    rss_urls = [
        "https://news.google.com/rss/search?q=NIFTY+OR+Sensex+OR+stock+market+OR+NSE+OR+BSE+when:6h&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=RBI+OR+inflation+OR+rupee+OR+banking+sector+when:6h&hl=en-IN&gl=IN&ceid=IN:en",
    ]
    
    # Financial keywords for filtering
    finance_keywords = [
        'nifty', 'sensex', 'stock', 'market', 'share', 'trading', 'equity',
        'rbi', 'reserve bank', 'rupee', 'inflation', 'gdp', 'economy', 'economic',
        'bse', 'nse', 'sebi', 'investor', 'investment', 'fund', 'mutual fund',
        'bank', 'financial', 'fiscal', 'monetary', 'interest rate', 'repo rate',
        'fii', 'dii', 'ipo', 'earnings', 'quarterly', 'revenue', 'profit',
        'commodity', 'crude oil', 'gold', 'forex', 'dollar', 'corporate'
    ]
    
    all_entries = []
    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)
        all_entries.extend(feed.entries)
    
    live_headlines = []
    
    for entry in all_entries[:30]:  # Check more entries
        # STRICT DATE FILTER: Only articles from last 6 hours
        if not is_article_fresh(entry, max_age_hours=6):
            continue
        
        headline = entry.title
        headline_lower = headline.lower()
        
        # Filter: Must contain finance keywords
        is_finance_related = any(keyword in headline_lower for keyword in finance_keywords)
        
        if not is_finance_related:
            continue
        
        # Get publication time for display
        pub_time = "Just now"
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                minutes_ago = int((datetime.now() - dt).total_seconds() / 60)
                if minutes_ago < 60:
                    pub_time = f"{minutes_ago}m ago"
                else:
                    hours_ago = minutes_ago // 60
                    pub_time = f"{hours_ago}h ago"
        except:
            pass
        
        # DETERMINISTIC sentiment scoring (same headline = same sentiment)
        score = analyze_sentiment(headline)
        live_headlines.append({
            "headline": headline,
            "sentiment": score,
            "impact": 3 if abs(score) > 0.7 else 2,
            "published": pub_time
        })
        
        # Collect top 5 finance-relevant headlines
        if len(live_headlines) >= 5:
            break
    
    return {"status": "success", "news": live_headlines}

@app.post("/predict")
def predict_market(data: NewsInput):
    return {
        "prediction": "Up" if data.sentiment_score > 0 else "Down",
        "confidence": 0.85,
        "action": "Buy Nifty" if data.sentiment_score > 0 else "Short/Wait"
    }

@app.get("/stock-data")
def get_stock_data(symbol: str = "^NSEI", period: str = "1d", interval: str = "5m"):
    """
    Fetch real-time stock data using yfinance.
    
    Args:
        symbol: Stock ticker (default: ^NSEI for NIFTY 50)
        period: Data period (1d, 5d, 1mo, etc.)
        interval: Data interval (1m, 5m, 15m, 1h, 1d)
    
    Returns:
        Time-series stock data with OHLCV
    """
    try:
        # Fetch data from yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Convert to frontend-friendly format
        chart_data = []
        for timestamp, row in df.iterrows():
            chart_data.append({
                "time": timestamp.strftime("%H:%M") if interval in ["1m", "5m", "15m", "30m", "1h"] else timestamp.strftime("%Y-%m-%d"),
                "price": round(row["Close"], 2),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "volume": int(row["Volume"])
            })
        
        # Calculate metrics
        latest_price = chart_data[-1]["price"]
        first_price = chart_data[0]["price"]
        price_change = latest_price - first_price
        price_change_pct = (price_change / first_price) * 100
        
        return {
            "status": "success",
            "symbol": symbol,
            "data": chart_data,
            "metrics": {
                "latest_price": latest_price,
                "price_change": round(price_change, 2),
                "price_change_pct": round(price_change_pct, 2),
                "high": round(df["High"].max(), 2),
                "low": round(df["Low"].min(), 2),
                "volume": int(df["Volume"].sum())
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")
@app.get("/predict-window")
def predict_time_window():
    """
    Rolling market mood aggregator with smart fallback strategy.
    
    Tries 2-hour window first, falls back to 6 hours if needed.
    
    Returns:
        - Net sentiment (weighted average)
        - Most impactful headline (guaranteed recent)
        - Bull/Bear ratio
        - Market prediction with confidence
    """
    try:
        # Financial keywords for relevance filtering
        finance_keywords = [
            'nifty', 'sensex', 'stock', 'market', 'share', 'trading', 'equity',
            'rbi', 'reserve bank', 'rupee', 'inflation', 'gdp', 'economy', 'economic',
            'bse', 'nse', 'sebi', 'investor', 'investment', 'fund', 'mutual fund',
            'bank', 'financial', 'fiscal', 'monetary', 'interest rate', 'repo rate',
            'fii', 'dii', 'ipo', 'earnings', 'quarterly', 'revenue', 'profit',
            'commodity', 'crude oil', 'gold', 'silver', 'forex', 'dollar',
            'corporate', 'company', 'ltd', 'limited', 'industry', 'sector'
        ]
        
        # Smart fallback: Try 2h first, then 6h if needed
        time_windows = [
            (2, "2h", "Last 2 Hours"),
            (6, "6h", "Last 6 Hours")
        ]
        
        articles = []
        all_entries = []
        time_window_used = "Last 2 Hours"
        is_fallback = False
        
        for max_hours, rss_param, window_label in time_windows:
            # Fetch news with appropriate time window
            rss_urls = [
                f"https://news.google.com/rss/search?q=NIFTY+OR+Sensex+OR+NSE+OR+BSE+OR+stock+market+when:{rss_param}&hl=en-IN&gl=IN&ceid=IN:en",
                f"https://news.google.com/rss/search?q=RBI+OR+inflation+OR+GDP+OR+rupee+OR+monetary+policy+when:{rss_param}&hl=en-IN&gl=IN&ceid=IN:en",
            ]
            
            all_entries = []
            for rss_url in rss_urls:
                feed = feedparser.parse(rss_url)
                all_entries.extend(feed.entries)
            
            if not all_entries:
                continue
            
            # Filter and process finance-relevant AND FRESH articles
            articles = []
            sentiments = []
            impacts = []
            weighted_sentiments = []
            
            for entry in all_entries[:40]:
                # Date freshness check
                if not is_article_fresh(entry, max_age_hours=max_hours):
                    continue
                
                headline = entry.title.lower()
                
                # Relevance check: Must contain at least one finance keyword
                is_finance_related = any(keyword in headline for keyword in finance_keywords)
                
                if not is_finance_related:
                    continue
                
                # Get human-readable publish time
                pub_time = "Just now"
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        minutes_ago = int((datetime.now() - dt).total_seconds() / 60)
                        if minutes_ago < 60:
                            pub_time = f"{minutes_ago}m ago"
                        else:
                            hours_ago = minutes_ago // 60
                            pub_time = f"{hours_ago}h ago"
                except:
                    pass
                
                # DETERMINISTIC sentiment scoring (same headline = same sentiment)
                score = analyze_sentiment(entry.title)
                
                # Calculate impact based on sentiment magnitude
                impact = 3 if abs(score) > 0.7 else (2 if abs(score) > 0.4 else 1)
                
                # Store data
                sentiments.append(score)
                impacts.append(impact)
                weighted_sentiments.append(score * impact)
                
                articles.append({
                    "headline": entry.title,
                    "sentiment": score,
                    "impact": impact,
                    "weighted_score": round(score * impact, 2),
                    "published": pub_time
                })
                
                if len(articles) >= 12:
                    break
            
            # If we found articles, use this time window
            if len(articles) > 0:
                time_window_used = window_label
                is_fallback = (max_hours > 2)
                break
        
        # Handle case where no finance-related articles found in any window
        if len(articles) == 0:
            return {
                "status": "no_data",
                "time_window": "Last 6 Hours",
                "articles_analyzed": 0,
                "message": "No finance-related news found. Market may be closed."
            }
        
        # 3. AGGREGATION PIPELINE - Calculate key metrics
        total_articles = len(sentiments)
        
        # Net sentiment (impact-weighted average)
        net_sentiment = sum(weighted_sentiments) / sum(impacts) if sum(impacts) > 0 else 0
        
        # Bull/Bear classification and ratio
        bullish_news = sum(1 for s in sentiments if s > 0.1)
        bearish_news = sum(1 for s in sentiments if s < -0.1)
        neutral_news = total_articles - bullish_news - bearish_news
        
        # Calculate Bull/Bear ratio (avoid division by zero)
        if bearish_news > 0:
            bull_bear_ratio = round(bullish_news / bearish_news, 2)
        else:
            bull_bear_ratio = float('inf') if bullish_news > 0 else 0
        
        # Find most impactful headline (highest absolute weighted score)
        most_impactful = max(articles, key=lambda x: abs(x["weighted_score"]))
        
        # 4. Market prediction logic
        if net_sentiment > 0.15:
            prediction = "Bullish"
            mood = "Positive"
            color = "green"
        elif net_sentiment < -0.15:
            prediction = "Bearish"
            mood = "Negative"
            color = "red"
        else:
            prediction = "Neutral"
            mood = "Mixed"
            color = "yellow"
        
        # Confidence calculation based on sentiment consistency
        sentiment_std = pd.Series(sentiments).std()
        base_confidence = 0.6
        sentiment_boost = min(abs(net_sentiment) * 0.3, 0.3)
        consistency_boost = max(0, (1 - sentiment_std) * 0.1) if sentiment_std < 1 else 0
        confidence = min(base_confidence + sentiment_boost + consistency_boost, 0.95)
        
        # 5. Market mood temperature (0-100 scale)
        # -1 (bearish) = 0, 0 (neutral) = 50, +1 (bullish) = 100
        temperature = round(((net_sentiment + 1) / 2) * 100, 1)

        return {
            "status": "success",
            "time_window": time_window_used,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "articles_analyzed": total_articles,
            "is_fallback": is_fallback,  # NEW: Indicates if using 6h fallback
            
            "sentiment_metrics": {
                "net_sentiment": round(net_sentiment, 3),
                "average_raw_sentiment": round(sum(sentiments) / total_articles, 3),
                "sentiment_std": round(sentiment_std, 3),
                "max_sentiment": round(max(sentiments), 2),
                "min_sentiment": round(min(sentiments), 2)
            },
            
            "market_breakdown": {
                "bullish_count": bullish_news,
                "bearish_count": bearish_news,
                "neutral_count": neutral_news,
                "bull_bear_ratio": bull_bear_ratio if bull_bear_ratio != float('inf') else "Inf",
                "bullish_pct": round((bullish_news / total_articles) * 100, 1),
                "bearish_pct": round((bearish_news / total_articles) * 100, 1)
            },
            
            "most_impactful_headline": {
                "headline": most_impactful["headline"],
                "sentiment": most_impactful["sentiment"],
                "impact": most_impactful["impact"],
                "weighted_score": most_impactful["weighted_score"],
                "published": most_impactful["published"]  # NEW: Include timestamp
            },
            
            "market_prediction": {
                "direction": prediction,
                "mood": mood,
                "color": color,
                "temperature": temperature,
                "confidence": round(confidence, 2)
            },
            
            "all_articles": articles[:10]  # Return top 10 for frontend display
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in aggregation pipeline: {str(e)}")
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)