import React, { useState, useEffect, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';


const STOCK_NAMES = {
  "AAPL": "Apple Inc.",
  "TSLA": "Tesla, Inc.",
  "NVDA": "NVIDIA Corporation",
  "AMZN": "Amazon.com, Inc.",
  "MSFT": "Microsoft Corp.",
  "AMD": "Advanced Micro Devices",
  "SPY": "SPDR S&P 500 ETF Trust",
  "COIN": "Coinbase Global, Inc.",
  "GOOGL": "Alphabet Inc.",
  "META": "Meta Platforms, Inc."
};

function Dashboard() {
  const [stockSymbol, setStockSymbol] = useState("AAPL");
  const [companyName, setCompanyName] = useState("Apple Inc.");
  const [priceData, setPriceData] = useState(null);
  const [fullHistory, setFullHistory] = useState([]); 
  const [chartData, setChartData] = useState([]);     
  const [trendingList, setTrendingList] = useState([]);
  const [searchText, setSearchText] = useState("");
  const [timeRange, setTimeRange] = useState("1Y");   

  const ws = useRef(null);

  // 1. WebSocket for Live Price
  useEffect(() => {
    if (ws.current) ws.current.close();
    ws.current = new WebSocket(`ws://localhost:8000/ws/stock/${stockSymbol}`);

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (!data.error) setPriceData(data);
    };

    return () => ws.current?.close();
  }, [stockSymbol]);

  // 2. Fetch History & Update Name
  useEffect(() => {
    // Set the name from our list, or just use the symbol if unknown
    setCompanyName(STOCK_NAMES[stockSymbol] || `${stockSymbol} Stock`);

    fetch(`http://localhost:8000/api/forecast/${stockSymbol}`)
      .then(res => res.json())
      .then(data => {
        if (data.history) {
          const formatted = data.history.map(item => ({
            date: new Date(item.ds),
            displayDate: new Date(item.ds).toLocaleDateString(),
            price: item.y
          }));
          setFullHistory(formatted);
        } else {
          setFullHistory([]);
        }
      })
      .catch(err => console.log("Graph error:", err));
  }, [stockSymbol]);

  // 3. Time Filter Logic (The 1W, 1M, 1Y Buttons)
  useEffect(() => {
    if (fullHistory.length === 0) {
      setChartData([]);
      return;
    }

    const now = new Date();
    let cutoff = new Date();

    if (timeRange === "1W") cutoff.setDate(now.getDate() - 7);
    if (timeRange === "1M") cutoff.setMonth(now.getMonth() - 1);
    if (timeRange === "1Y") cutoff.setFullYear(now.getFullYear() - 1);
    if (timeRange === "ALL") cutoff = new Date(0); // 1970

    // Filter data based on date
    const filtered = fullHistory.filter(item => item.date >= cutoff);
    setChartData(filtered);

  }, [timeRange, fullHistory]);

  // 4. Trending List
  useEffect(() => {
    fetch("http://localhost:8000/api/trending")
      .then(res => res.json())
      .then(data => setTrendingList(data))
      .catch(err => console.log("Trending error:", err));
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchText.trim() !== "") {
      setStockSymbol(searchText.toUpperCase());
      setPriceData(null); 
      setFullHistory([]);
      setSearchText("");
    }
  };

  return (
    <div className="app-container">
      
      {/* MAIN DASHBOARD */}
      <div className="main-section">
        
        {/* Search Bar */}
        <form className="search-box" onSubmit={handleSearch}>
          <input 
            className="search-input"
            type="text" 
            placeholder="Search stock (e.g. TSLA)..." 
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <button className="search-btn">SEARCH</button>
        </form>

        {/* Header: Name, Price, AI Badge */}
        <div className="stock-header">
          <div className="stock-info">
            <h1>
              {stockSymbol} 
              <span className="ai-badge">✨ AI Forecast</span>
            </h1>
            <div className="company-name">{companyName}</div>
          </div>

          <div className="price-right">
            {priceData ? (
              <>
                <div className="big-price">${priceData.price}</div>
                <div className={priceData.change >= 0 ? "green-text" : "red-text"}>
                  {priceData.change > 0 ? "▲" : "▼"} {priceData.change.toFixed(2)}%
                </div>
              </>
            ) : (
              <div className="gray-text">Loading...</div>
            )}
          </div>
        </div>

        {/* Graph Section */}
        <div className="chart-box">
          <div className="chart-header">
            <h3>Price History</h3>
            
            {/* The Time Buttons */}
            <div className="time-controls">
              {["1W", "1M", "1Y", "ALL"].map(range => (
                <button 
                  key={range}
                  className={`time-btn ${timeRange === range ? "active" : ""}`}
                  onClick={() => setTimeRange(range)}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>

          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorBlue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="displayDate" tick={{fontSize: 12, fill: '#94a3b8'}} minTickGap={30} />
              <YAxis domain={['auto', 'auto']} tick={{fontSize: 12, fill: '#94a3b8'}} />
              <Tooltip 
                contentStyle={{backgroundColor: '#1e293b', borderRadius: '10px', border: 'none'}}
                itemStyle={{color: '#fff'}}
                labelStyle={{color: '#94a3b8'}}
              />
              <Area 
                type="monotone" 
                dataKey="price" 
                stroke="#3b82f6" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorBlue)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* RIGHT SIDEBAR */}
      <div className="sidebar">
        <h3 className="gray-text" style={{fontSize: '14px', textTransform: 'uppercase'}}>Trending Now</h3>
        {trendingList.map((stock) => (
          <div 
            key={stock.symbol} 
            className="stock-item" 
            onClick={() => {
              setStockSymbol(stock.symbol);
              setPriceData(null);
            }}
          >
            <div>
              <strong>{stock.symbol}</strong>
              <div style={{fontSize: '12px', color: '#94a3b8'}}>
                {STOCK_NAMES[stock.symbol] || "Stock"}
              </div>
            </div>
            <div className={stock.change >= 0 ? "green-text" : "red-text"}>
              ${stock.price}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}

export default Dashboard;