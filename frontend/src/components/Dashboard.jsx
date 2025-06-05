import React, { useState, useEffect } from 'react';
import { RefreshCw, Calendar, Clock, AlertTriangle, CheckCircle, XCircle, Minus } from 'lucide-react';

const FeedMonitorDashboard = () => {
  const [feedsData, setFeedsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [error, setError] = useState(null);

  // Status color mapping to match expected design
  const getStatusColor = (status) => {
    switch (status) {
      case 'received': return 'bg-green-500';
      case 'delayed': return 'bg-yellow-500';
      case 'missing': return 'bg-red-400';
      case 'partial': return 'bg-orange-500';
      case 'failed': return 'bg-red-600';
      default: return 'bg-gray-300';
    }
  };

  // Status icons
  const getStatusIcon = (status) => {
    const iconClass = "w-5 h-5 text-white";
    switch (status) {
      case 'received': return <CheckCircle className={iconClass} />;
      case 'delayed': return <Clock className={iconClass} />;
      case 'missing': return <XCircle className={iconClass} />;
      case 'partial': return <AlertTriangle className={iconClass} />;
      case 'failed': return <XCircle className={iconClass} />;
      default: return <Minus className={iconClass} />;
    }
  };

  const fetchFeedsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Simulate API response with 14 days of data
      const mockData = [
        {
          feed_name: "Customer Transactions",
          daily_status: generateMockDailyStatus("Customer Transactions")
        },
        {
          feed_name: "Product Catalog",
          daily_status: generateMockDailyStatus("Product Catalog")
        },
        {
          feed_name: "Order Processing",
          daily_status: generateMockDailyStatus("Order Processing")
        }
      ];
      
      setFeedsData(mockData);
      setLastUpdate(new Date());
      
    } catch (err) {
      setError('Failed to fetch feed data');
      console.error('Error fetching feeds:', err);
    } finally {
      setLoading(false);
    }
  };

  // Generate mock data for 14 days
  const generateMockDailyStatus = (feedName) => {
    const dailyStatus = {};
    const today = new Date();
    
    for (let i = 0; i < 14; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'short' });
      const isWeekend = date.getDay() === 0 || date.getDay() === 6;
      
      let status = 'received';
      let count = Math.floor(Math.random() * 1000) + 500;
      
      // Simulate some issues
      if (Math.random() < 0.1) {
        status = 'missing';
        count = 0;
      } else if (Math.random() < 0.15) {
        status = 'partial';
        count = Math.floor(Math.random() * 300) + 100;
      } else if (Math.random() < 0.08) {
        status = 'delayed';
      }
      
      // Weekend logic for Customer Transactions
      if (isWeekend && feedName === "Customer Transactions") {
        status = 'received';
        count = 0;
      }
      
      dailyStatus[dateStr] = {
        status: status,
        count: count,
        day_of_week: dayOfWeek,
        is_weekend: isWeekend
      };
    }
    
    return dailyStatus;
  };

  // Generate date headers for 14 days
  const generateDateHeaders = () => {
    const headers = [];
    const today = new Date();
    
    for (let i = 13; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      headers.push({
        date: date.toISOString().split('T')[0],
        day: date.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase(),
        dayNum: date.getDate(),
        isWeekend: date.getDay() === 0 || date.getDay() === 6
      });
    }
    
    return headers;
  };

  const manualRefresh = async () => {
    await fetchFeedsData();
  };

  useEffect(() => {
    fetchFeedsData();
    
    // Auto-refresh every 10 minutes
    const interval = setInterval(fetchFeedsData, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const dateHeaders = generateDateHeaders();

  if (loading && feedsData.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">Loading feed data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 rounded-lg mb-6">
        <div className="px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Feed Monitor Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">
                Last updated: {lastUpdate.toLocaleString()}
              </p>
            </div>
            <button
              onClick={manualRefresh}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Status Legend */}
      <div className="bg-white rounded-lg shadow-sm mb-6 p-4">
        <div className="flex items-center space-x-6">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
            <span className="text-sm text-gray-700">Received</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-yellow-500 rounded mr-2"></div>
            <span className="text-sm text-gray-700">Delayed</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-orange-500 rounded mr-2"></div>
            <span className="text-sm text-gray-700">Partial</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-400 rounded mr-2"></div>
            <span className="text-sm text-gray-700">Missing</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-600 rounded mr-2"></div>
            <span className="text-sm text-gray-700">Failed</span>
          </div>
        </div>
      </div>

      {/* Feed Status Grid */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="text-left py-3 px-4 font-medium text-gray-600 sticky left-0 bg-gray-50 z-10 min-w-[150px]">
                  FEED NAME
                </th>
                {dateHeaders.map((header) => (
                  <th
                    key={header.date}
                    className={`text-center py-3 px-2 font-medium text-xs min-w-[60px] ${
                      header.isWeekend ? 'bg-gray-100 text-gray-400' : 'text-gray-600'
                    }`}
                  >
                    <div className="flex flex-col items-center">
                      <span className="text-xs">{header.day}</span>
                      <span className="text-sm font-bold">{header.dayNum}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {feedsData.map((feed, feedIndex) => (
                <tr key={feed.feed_name} className="border-b hover:bg-gray-50">
                  <td className="py-4 px-4 font-medium text-gray-900 sticky left-0 bg-white hover:bg-gray-50 z-10 border-r">
                    {feed.feed_name}
                  </td>
                  {dateHeaders.map((header) => {
                    const dayData = feed.daily_status[header.date];
                    return (
                      <td
                        key={header.date}
                        className="py-4 px-2 text-center"
                        title={`${feed.feed_name} - ${header.date}\nStatus: ${dayData?.status || 'unknown'}\nRecords: ${dayData?.count || 0}`}
                      >
                        <div className="flex flex-col items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            getStatusColor(dayData?.status || 'unknown')
                          }`}>
                            {getStatusIcon(dayData?.status || 'unknown')}
                          </div>
                          <div className="text-xs text-gray-600 mt-1 font-medium">
                            {dayData?.count || 0}
                          </div>
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-full">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Feeds Healthy Today</p>
              <p className="text-2xl font-bold text-gray-900">
                {feedsData.length > 0 ? 
                  feedsData.filter(feed => {
                    const today = new Date().toISOString().split('T')[0];
                    return feed.daily_status[today]?.status === 'received';
                  }).length : 0
                } / {feedsData.length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-full">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Next Check In</p>
              <p className="text-2xl font-bold text-gray-900">
                {Math.max(0, Math.floor((10 * 60 * 1000 - (Date.now() - lastUpdate.getTime())) / 60000))}m
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-full">
              <Calendar className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Monitoring Period</p>
              <p className="text-2xl font-bold text-gray-900">14 Days</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeedMonitorDashboard;