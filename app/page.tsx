"use client";

import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown, Activity, AlertCircle, Thermometer, RefreshCw } from "lucide-react";

export default function Dashboard() {
  // 1. All state variables consolidated
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [sentiment, setSentiment] = useState(0.8);
  const [impact, setImpact] = useState(3);
  const [liveNews, setLiveNews] = useState<any[]>([]);
  const [newsLoading, setNewsLoading] = useState(true);
  
  // NEW: Market mood and stock data state
  const [marketMood, setMarketMood] = useState<any>(null);
  const [moodLoading, setMoodLoading] = useState(true);
  const [stockData, setStockData] = useState<any[]>([]);
  const [stockMetrics, setStockMetrics] = useState<any>(null);
  const [stockLoading, setStockLoading] = useState(true);

  // 2. Fetch live news on load
  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/live-news");
        const data = await response.json();
        setLiveNews(data.news || []);
      } catch (error) {
        console.error("Failed to fetch news", error);
        setLiveNews([]);
      }
      setNewsLoading(false);
    };
    fetchNews();
  }, []);

  // 3. Fetch market mood aggregator (polls every 60 seconds)
  useEffect(() => {
    const fetchMarketMood = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/predict-window");
        const data = await response.json();
        setMarketMood(data);
      } catch (error) {
        console.error("Failed to fetch market mood", error);
        setMarketMood(null);
      }
      setMoodLoading(false);
    };
    
    fetchMarketMood(); // Initial fetch
    const interval = setInterval(fetchMarketMood, 60000); // Poll every 60 seconds
    return () => clearInterval(interval);
  }, []);

  // 4. Fetch real stock data from yfinance
  useEffect(() => {
    const fetchStockData = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/stock-data?symbol=^NSEI&period=1d&interval=5m");
        const data = await response.json();
        if (data.status === "success") {
          setStockData(data.data);
          setStockMetrics(data.metrics);
        }
      } catch (error) {
        console.error("Failed to fetch stock data", error);
        setStockData([]);
      }
      setStockLoading(false);
    };
    
    fetchStockData();
    const interval = setInterval(fetchStockData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, []);

  // 5. API Prediction Logic
  const testAPI = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sentiment_score: sentiment,
          impact_numeric: impact,
          sector_tech: 1
        }),
      });
      const data = await response.json();
      setPrediction(data);
    } catch (error) {
      console.error("API Connection Failed", error);
    }
    setLoading(false);
  };

  // Helper function for temperature color
  const getTempColor = (temp: number) => {
    if (temp >= 60) return "from-emerald-500 to-green-600";
    if (temp >= 45) return "from-yellow-500 to-amber-600";
    return "from-red-500 to-rose-600";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-8 font-sans">
      
      {/* Header */}
      <header className="mb-8 border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity className="text-emerald-400" />
          Macro-Event Sentiment Engine
        </h1>
        <p className="text-slate-400 mt-2">Production-Ready Time-Series Market Intelligence</p>
      </header>

      {/* NEW: Market Thermometer - Top Summary Card */}
      {marketMood && marketMood.status === "success" && (
        <div className="mb-8 bg-gradient-to-r from-slate-900 to-slate-800 border border-slate-700 p-6 rounded-xl shadow-2xl">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                <Thermometer className="text-blue-400" size={28} />
                Market Thermometer
                <span className="text-sm font-normal text-slate-400 ml-2">
                  ({marketMood.time_window} · {marketMood.articles_analyzed} articles)
                  {marketMood.is_fallback && <span className="text-yellow-400 ml-2">⚠️ Slow news period</span>}
                </span>
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Temperature Gauge */}
                <div className="text-center">
                  <div className="text-5xl font-black mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    {marketMood.market_prediction.temperature}°
                  </div>
                  <div className="text-sm text-slate-400">Market Temperature</div>
                  <div className={`mt-2 h-2 rounded-full bg-gradient-to-r ${getTempColor(marketMood.market_prediction.temperature)}`}></div>
                </div>

                {/* Sentiment Score */}
                <div className="text-center">
                  <div className={`text-4xl font-bold mb-2 ${marketMood.sentiment_metrics.net_sentiment > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {marketMood.sentiment_metrics.net_sentiment > 0 ? '+' : ''}{marketMood.sentiment_metrics.net_sentiment}
                  </div>
                  <div className="text-sm text-slate-400">Net Sentiment</div>
                  <div className="text-xs text-slate-500 mt-1">
                    {marketMood.market_prediction.mood} Market
                  </div>
                </div>

                {/* Bull/Bear Ratio */}
                <div className="text-center">
                  <div className="text-3xl font-bold mb-2 text-blue-400">
                    {typeof marketMood.market_breakdown.bull_bear_ratio === 'number' 
                      ? marketMood.market_breakdown.bull_bear_ratio 
                      : '∞'}
                  </div>
                  <div className="text-sm text-slate-400">Bull/Bear Ratio</div>
                  <div className="flex justify-center gap-2 mt-2 text-xs">
                    <span className="text-emerald-400">🐂 {marketMood.market_breakdown.bullish_count}</span>
                    <span className="text-slate-500">·</span>
                    <span className="text-red-400">🐻 {marketMood.market_breakdown.bearish_count}</span>
                  </div>
                </div>

                {/* Prediction */}
                <div className="text-center">
                  <div className={`text-2xl font-bold mb-2 flex items-center justify-center gap-2 ${
                    marketMood.market_prediction.direction === 'Bullish' ? 'text-emerald-400' : 
                    marketMood.market_prediction.direction === 'Bearish' ? 'text-red-400' : 'text-yellow-400'
                  }`}>
                    {marketMood.market_prediction.direction === 'Bullish' ? <TrendingUp size={28} /> : 
                     marketMood.market_prediction.direction === 'Bearish' ? <TrendingDown size={28} /> : <Activity size={28} />}
                    {marketMood.market_prediction.direction}
                  </div>
                  <div className="text-sm text-slate-400">Market Direction</div>
                  <div className="text-xs text-slate-500 mt-1">
                    {(marketMood.market_prediction.confidence * 100).toFixed(0)}% confidence
                  </div>
                </div>
              </div>

              {/* Most Impactful Headline */}
              <div className="mt-6 p-4 bg-slate-950 rounded-lg border border-slate-700">
                <div className="text-xs text-slate-500 mb-2 flex items-center gap-2">
                  <AlertCircle size={14} />
                  Most Impactful Headline (Impact Score: {marketMood.most_impactful_headline.weighted_score})
                  {marketMood.most_impactful_headline.published && (
                    <span className="ml-2 text-blue-400">· {marketMood.most_impactful_headline.published}</span>
                  )}
                </div>
                <p className="text-sm text-slate-200 font-medium">{marketMood.most_impactful_headline.headline}</p>
                <div className="mt-2 flex items-center gap-4 text-xs">
                  <span className={marketMood.most_impactful_headline.sentiment > 0 ? 'text-emerald-400' : 'text-red-400'}>
                    Sentiment: {marketMood.most_impactful_headline.sentiment > 0 ? '+' : ''}{marketMood.most_impactful_headline.sentiment}
                  </span>
                  <span className="text-slate-500">Impact: {marketMood.most_impactful_headline.impact}/3</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: API Control Panel */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg h-fit">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <AlertCircle size={20} className="text-blue-400" />
            Simulate News Event
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">FinBERT Sentiment Score (-1 to 1)</label>
              <input 
                type="number" step="0.1" value={sentiment ?? 0} 
                onChange={(e) => setSentiment(parseFloat(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
              />
            </div>
            
            <div>
              <label className="block text-sm text-slate-400 mb-1">Impact Level (1=Low, 3=High)</label>
              <select 
                value={impact} onChange={(e) => setImpact(parseInt(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
              >
                <option value={1}>1 - Low Impact</option>
                <option value={2}>2 - Medium Impact</option>
                <option value={3}>3 - High Impact</option>
              </select>
            </div>

            <button 
              onClick={testAPI}
              className="w-full mt-4 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded transition-colors disabled:opacity-50"
              disabled={loading}
            >
              {loading ? "Running AI Model..." : "Predict Market Reaction"}
            </button>
          </div>

          {/* API Result Card */}
          {prediction && (
            <div className={`mt-6 p-4 rounded-lg border ${prediction.prediction === "Up" ? "bg-emerald-900/30 border-emerald-800" : "bg-red-900/30 border-red-800"}`}>
              <h3 className="text-sm text-slate-400 mb-1">XGBoost Prediction</h3>
              <div className="flex items-center gap-3">
                {prediction.prediction === "Up" ? <TrendingUp className="text-emerald-400" size={32}/> : <TrendingDown className="text-red-400" size={32}/>}
                <div>
                  <p className="text-2xl font-bold">{prediction.action}</p>
                  <p className="text-sm text-slate-400">Confidence: {prediction.confidence * 100}%</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Charts & Feed */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Chart Widget - Real Stock Data */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">NIFTY 50 Live Intraday (^NSEI)</h2>
              {stockMetrics && (
                <div className="text-right">
                  <div className={`text-2xl font-bold ${stockMetrics.price_change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    ₹{stockMetrics.latest_price}
                  </div>
                  <div className={`text-sm ${stockMetrics.price_change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {stockMetrics.price_change >= 0 ? '+' : ''}{stockMetrics.price_change} ({stockMetrics.price_change_pct >= 0 ? '+' : ''}{stockMetrics.price_change_pct}%)
                  </div>
                </div>
              )}
            </div>
            
            <div className="h-64 w-full">
              {stockLoading ? (
                <div className="flex items-center justify-center h-full">
                  <RefreshCw className="animate-spin text-blue-400" size={32} />
                  <span className="ml-3 text-slate-400">Loading live market data...</span>
                </div>
              ) : stockData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={stockData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="time" stroke="#94a3b8" />
                    <YAxis domain={['auto', 'auto']} stroke="#94a3b8" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                      labelStyle={{ color: '#94a3b8' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="price" 
                      stroke={stockMetrics?.price_change >= 0 ? '#34d399' : '#ef4444'} 
                      strokeWidth={3} 
                      dot={{ r: 3, fill: stockMetrics?.price_change >= 0 ? '#34d399' : '#ef4444' }} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-slate-400">
                  No market data available. Market may be closed.
                </div>
              )}
            </div>
            
            {stockMetrics && (
              <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-slate-500">High</div>
                  <div className="text-slate-200 font-semibold">₹{stockMetrics.high}</div>
                </div>
                <div>
                  <div className="text-slate-500">Low</div>
                  <div className="text-slate-200 font-semibold">₹{stockMetrics.low}</div>
                </div>
                <div>
                  <div className="text-slate-500">Volume</div>
                  <div className="text-slate-200 font-semibold">{(stockMetrics.volume / 1000000).toFixed(2)}M</div>
                </div>
                <div>
                  <div className="text-slate-500">Data Points</div>
                  <div className="text-slate-200 font-semibold">{stockData.length}</div>
                </div>
              </div>
            )}
          </div>

          {/* Live News Feed with Optional Chaining Fix */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Activity size={20} className="text-blue-400" />
              Live Market Feed (Last 24h)
            </h2>
            
            <div className="space-y-3">
              {newsLoading ? (
                <p className="text-slate-400 animate-pulse">Scraping financial news...</p>
              ) : (
                liveNews?.map((item: any, index: number) => (
                  <div 
                    key={index} 
                    className={`p-3 border-l-4 rounded bg-slate-950 ${
                      item.sentiment > 0 ? 'border-emerald-500' : 'border-red-500'
                    }`}
                  >
                    <p className="font-medium text-slate-200 text-sm">{item.headline}</p>
                    <div className="flex justify-between items-center mt-2">
                      <span className={`text-xs font-mono ${item.sentiment > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        FinBERT: {item.sentiment > 0 ? '+' : ''}{item.sentiment}
                      </span>
                      
                      <button 
                        onClick={() => {
                          setSentiment(item.sentiment);
                          setImpact(item.impact);
                        }}
                        className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded transition-colors"
                      >
                        Analyze This
                      </button>
                    </div>
                  </div>
                ))
              )}
              {!newsLoading && liveNews?.length === 0 && (
                <p className="text-slate-500 text-sm italic">No recent news events found or API is offline.</p>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}