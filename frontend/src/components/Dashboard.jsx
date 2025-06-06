import React, { useState, useEffect } from 'react';
import { RefreshCw, Calendar, Clock, AlertTriangle, CheckCircle, XCircle, Minus } from 'lucide-react';

const FeedMonitorDashboard = () => {
  const [feedsData, setFeedsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [error, setError] = useState(null);

  // Status color mapping
  const getStatusColor = (status) => {
    switch (status) {
      case 'received': return 'bg-green-500';
      case 'delayed': return 'bg-yellow-500';
      case 'missing': return 'bg-red-500';
      case 'partial': return 'bg-orange-500';
      case 'failed': return 'bg-red-600';
      default: return 'bg-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'received': return <CheckCircle className="w-3 h-3 text-white" />;
      case 'delayed': return <Clock className="w-3 h-3 text-white" />;
      case 'missing': return <XCircle className="w-3 h-3 text-white" />;
      case 'partial': return <AlertTriangle className="w-3 h-3 text-white" />;
      case 'failed': return <XCircle className="w-3 h-3 text-white" />;
      default: return <Minus className="w-3 h-3 text-white" />;
    }
  };

  const fetchFeedsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Simulate API response
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

  // Generate mock data for demonstration
  const generateMockDailyStatus = (feedName) => {
    const dailyStatus = {};
    const today = new Date();
    
    for (let i = 0; i < 30; i++) {
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
      
      // Weekend logic
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

  // Generate date headers
  const generateDateHeaders = () => {
    const headers = [];
    const today = new Date();
    
    for (let i = 0; i < 30; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      headers.push({
        date: date.toISOString().split('T')[0],
        day: date.toLocaleDateString('en-US', { weekday: 'short' }),
        dayNum: date.getDate(),
        isWeekend: date.getDay() === 0 || date.getDay() === 6
      });
    }
    
    return headers.reverse();
  };

  const manualRefresh = async () => {
    try {
      await fetchFeedsData();
    } catch (err) {
      setError('Failed to refresh data');
    }
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Feed Monitor Dashboard</h1>
              <p className="text-sm text-gray-500">
                Last updated: {lastUpdate.toLocaleString()}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {error && (
                <div className="text-red-600 text-sm flex items-center">
                  <AlertTriangle className="w-4 h-4 mr-1" />
                  {error}
                </div>
              )}
              <button
                onClick={manualRefresh}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Legend */}
        <div className="bg-white rounded-lg shadow mb-6 p-4">
          <h3 className="text-lg font-semibold mb-3">Status Legend</h3>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center">
              <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
              <span className="text-sm">Received</span>
            </div>
            <div className="flex items-center">
              <Clock className="w-4 h-4 text-yellow-500 mr-2" />
              <span className="text-sm">Delayed</span>
            </div>
            <div className="flex items-center">
              <AlertTriangle className="w-4 h-4 text-orange-500 mr-2" />
              <span className="text-sm">Partial</span>
            </div>
            <div className="flex items-center">
              <XCircle className="w-4 h-4 text-red-500 mr-2" />
              <span className="text-sm">Missing</span>
            </div>
            <div className="flex items-center">
              <XCircle className="w-4 h-4 text-red-600 mr-2" />
              <span className="text-sm">Failed</span>
            </div>
          </div>
        </div>

        {/* Feed Status Grid */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="sticky left-0 bg-gray-50 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r z-10">
                    Feed Name
                  </th>
                  {dateHeaders.map((header) => (
                    <th
                      key={header.date}
                      className={`px-2 py-3 text-center text-xs font-medium uppercase tracking-wider min-w-[50px] ${
                        header.isWeekend ? 'bg-gray-100 text-gray-400' : 'text-gray-500'
                      }`}
                    >
                      <div>
                        <div>{header.day}</div>
                        <div className="text-sm font-bold">{header.dayNum}</div>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {feedsData.map((feed, feedIndex) => (
                  <tr key={feed.feed_name} className={feedIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className={`sticky left-0 px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-r z-10 ${
                      feedIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                    }`}>
                      {feed.feed_name}
                    </td>
                    {dateHeaders.map((header) => {
                      const dayData = feed.daily_status[header.date];
                      const status = dayData?.status || 'unknown';
                      const count = dayData?.count || 0;
                      
                      return (
                        <td
                          key={header.date}
                          className="px-2 py-4 text-center"
                          title={`${feed.feed_name} - ${header.date}: ${status} (${count} records)`}
                        >
                          <div className="flex flex-col items-center">
                            <div className={`w-6 h-6 rounded-full flex items-center justify-center ${getStatusColor(status)}`}>
                              {getStatusIcon(status)}
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              {count}
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
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-500 mr-3" />
              <div>
                <p className="text-sm text-gray-500">Feeds Healthy Today</p>
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
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <Clock className="w-8 h-8 text-blue-500 mr-3" />
              <div>
                <p className="text-sm text-gray-500">Next Check In</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.max(0, Math.floor((10 * 60 * 1000 - (Date.now() - lastUpdate.getTime())) / 60000))}m
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <Calendar className="w-8 h-8 text-purple-500 mr-3" />
              <div>
                <p className="text-sm text-gray-500">Monitoring Period</p>
                <p className="text-2xl font-bold text-gray-900">30 Days</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default FeedMonitorDashboard;