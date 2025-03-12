'use client';

import { useEffect, useState } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

interface UsageStats {
  name: string;
  recordCount: number;
}

interface DailyStats {
  date: string;
  count: number;
}

interface UserGrowthStats {
  date: string;
  totalUsers: number;
}

interface ProductDailyStats {
  date: string;
  product: string;
  count: number;
}

interface UserDailyStats {
  date: string;
  name: string;
  count: number;
}

// 注册Chart.js组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// 添加全局动画样式
const globalStyles = `
  @keyframes float {
    0% { transform: translate(0, 0) rotate(0deg); }
    25% { transform: translate(10px, -10px) rotate(5deg); }
    50% { transform: translate(0, -20px) rotate(0deg); }
    75% { transform: translate(-10px, -10px) rotate(-5deg); }
    100% { transform: translate(0, 0) rotate(0deg); }
  }

  @keyframes pulse {
    0% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.2); opacity: 0.8; }
    100% { transform: scale(1); opacity: 0.5; }
  }

  @keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
  }

  @keyframes slideIn {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }
`;

export default function UsagePage() {
  const [userStats, setUserStats] = useState<UsageStats[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [userGrowthStats, setUserGrowthStats] = useState<UserGrowthStats[]>([]);
  const [productDailyStats, setProductDailyStats] = useState<ProductDailyStats[]>([]);
  const [userDailyStats, setUserDailyStats] = useState<UserDailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState(new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16));
  const [endTime, setEndTime] = useState(new Date().toISOString().slice(0, 16));
  const [excludeUsers, setExcludeUsers] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(0);

  useEffect(() => {
    // 添加全局样式
    const styleSheet = document.createElement('style');
    styleSheet.textContent = globalStyles;
    document.head.appendChild(styleSheet);
    return () => styleSheet.remove();
  }, []);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/usage/auth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
      });

      if (response.ok) {
        setIsAuthenticated(true);
        setAuthError(null);
      } else {
        setAuthError('密码错误，请重试');
      }
    } catch (error) {
      setAuthError('验证过程出错，请重试');
    }
  };

  // Chart data configurations...
  const userChartData = {
    labels: userStats.map(stat => stat.name || '匿名用户'),
    datasets: [{
      label: '访问次数',
      data: userStats.map(stat => stat.recordCount),
      backgroundColor: 'rgba(75, 192, 192, 0.5)',
      borderColor: 'rgb(75, 192, 192)',
      borderWidth: 1
    }]
  };

  const dailyStatsChartData = {
    labels: dailyStats.map(stat => stat.date),
    datasets: [{
      label: '每日访问量',
      data: dailyStats.map(stat => stat.count),
      borderColor: 'rgb(255, 159, 64)',
      backgroundColor: 'rgba(255, 159, 64, 0.5)',
      tension: 0.4,
      fill: true
    }]
  };

  const userGrowthChartData = {
    labels: userGrowthStats.map(stat => stat.date),
    datasets: [{
      label: '累计用户数',
      data: userGrowthStats.map(stat => stat.totalUsers),
      borderColor: 'rgb(153, 102, 255)',
      backgroundColor: 'rgba(153, 102, 255, 0.5)',
      tension: 0.4,
      fill: true
    }]
  };

  const productDailyChartData = {
    labels: [...new Set(productDailyStats.map(stat => stat.date))].sort(),
    datasets: [...new Set(productDailyStats.map(stat => stat.product))].map(product => {
      const dates = [...new Set(productDailyStats.map(stat => stat.date))].sort();
      return {
        label: product,
        data: dates.map(date => ({
          x: date,
          y: productDailyStats.find(stat => stat.date === date && stat.product === product)?.count || 0
        })),
        backgroundColor: `hsla(${Math.random() * 360}, 70%, 50%, 0.5)`,
        borderColor: `hsla(${Math.random() * 360}, 70%, 50%, 1)`,
        tension: 0.4
      };
    })
  };

  const userDailyChartData = {
    labels: [...new Set(userDailyStats.map(stat => stat.date))].sort(),
    datasets: [...new Set(userDailyStats.map(stat => stat.name))].map(name => {
      const dates = [...new Set(userDailyStats.map(stat => stat.date))].sort();
      return {
        label: name,
        data: dates.map(date => ({
          x: date,
          y: userDailyStats.find(stat => stat.date === date && stat.name === name)?.count || 0
        })),
        backgroundColor: `hsla(${Math.random() * 360}, 70%, 50%, 0.5)`,
        borderColor: `hsla(${Math.random() * 360}, 70%, 50%, 1)`,
        tension: 0.4
      };
    })
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#E5E7EB'
        }
      },
      title: {
        display: true,
        color: '#E5E7EB'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(229, 231, 235, 0.1)'
        },
        ticks: {
          color: '#E5E7EB'
        }
      },
      x: {
        grid: {
          color: 'rgba(229, 231, 235, 0.1)'
        },
        ticks: {
          color: '#E5E7EB'
        }
      }
    },
    animation: {
      duration: 2000,
      easing: 'easeInOutQuart' as const
    }
  };

  const fetchData = async () => {
    setLoading(true);
    setLoadingProgress(0);
    try {
      const response = await fetch(`/api/usage?startTime=${startTime}&endTime=${endTime}&excludeUsers=${excludeUsers}`);
      if (!response.ok) {
        throw new Error('Failed to fetch usage statistics');
      }
      const data = await response.json();
      
      // 模拟加载进度
      let progress = 0;
      const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) {
          progress = 100;
          clearInterval(progressInterval);
        }
        setLoadingProgress(progress);
      }, 200);

      // 延迟设置数据以展示加载动画
      setTimeout(() => {
        setUserStats(data.userStats);
        setDailyStats(data.dailyStats);
        setUserGrowthStats(data.userGrowthStats || []);
        setProductDailyStats(data.productDailyStats || []);
        setUserDailyStats(data.userDailyStats || []);
        setLoading(false);
        clearInterval(progressInterval);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [startTime, endTime, isAuthenticated]);

  const LoadingOverlay = () => {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="relative">
          {/* 进度条背景 */}
          <div className="w-64 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-yellow-500 to-purple-500 transition-all duration-300"
              style={{ width: `${loadingProgress}%` }}
            />
          </div>
          {/* 进度文字 */}
          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-yellow-500 font-mono">
            {Math.round(loadingProgress)}%
          </div>
          {/* 装饰性粒子 */}
          <div className="absolute -inset-10 pointer-events-none">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="absolute w-3 h-3 bg-yellow-500"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animation: `pulse ${Math.random() * 2 + 1}s infinite`,
                  opacity: Math.random() * 0.5 + 0.3
                }}
              />
            ))}
          </div>
        </div>
      </div>
    );
  };

  // 骨架屏组件
  const ChartSkeleton = () => {
    return (
      <div className="animate-pulse space-y-4 relative overflow-hidden">
        <div className="h-8 bg-gray-700/50 rounded w-1/4 mb-6"></div>
        <div className="h-[300px] bg-gray-700/50 rounded relative">
          <div 
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"
            style={{
              backgroundSize: '200% 100%',
              animation: 'shimmer 2s infinite'
            }}
          />
        </div>
      </div>
    );
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background-primary p-8 flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {Array.from({ length: 50 }).map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 bg-yellow-500/30 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animation: `float ${Math.random() * 10 + 5}s linear infinite`,
                opacity: Math.random(),
                transform: `scale(${Math.random() * 2})`
              }}
            />
          ))}
        </div>
        <div className="max-w-md w-full space-y-8 relative">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 blur-3xl" />
          <div className="relative">
            <h2 className="text-center text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400 animate-pulse">
              访问验证
            </h2>
            <form onSubmit={handleAuth} className="mt-8 space-y-6">
              <div>
                <label className="block text-lg font-medium text-yellow-400 mb-2">
                  天王盖地虎
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none relative block w-full px-3 py-2 border border-yellow-300/30 bg-black/50 text-yellow-400 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                  placeholder="请输入暗号"
                  required
                />
              </div>
              {authError && (
                <div className="text-red-500 text-sm">{authError}</div>
              )}
              <div>
                <button
                  type="submit"
                  className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-black bg-yellow-400 hover:bg-yellow-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 transition-colors duration-300"
                >
                  验证
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background-primary p-8 relative overflow-hidden transition-all duration-500">
      {loading && <LoadingOverlay />}
      <div className="max-w-6xl mx-auto relative z-10">
        <h1 className="text-2xl font-bold mb-6 text-text-primary transition-all duration-300 transform hover:scale-105">
          用户访问统计
        </h1>

        <div className="mt-8 transition-all duration-300">
          <div className="flex gap-4 items-center flex-wrap">
            <div className="transition-all duration-300 hover:scale-105">
              <label htmlFor="startTime" className="mr-2 text-yellow-400">开始时间:</label>
              <input
                type="datetime-local"
                id="startTime"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="p-2 bg-black/50 text-yellow-400 border border-yellow-400/30 rounded focus:outline-none focus:ring-2 focus:ring-yellow-500 transition-all duration-300"
              />
            </div>
            <div className="transition-all duration-300 hover:scale-105">
              <label htmlFor="endTime" className="mr-2 text-yellow-400">结束时间:</label>
              <input
                type="datetime-local"
                id="endTime"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="p-2 bg-black/50 text-yellow-400 border border-yellow-400/30 rounded focus:outline-none focus:ring-2 focus:ring-yellow-500 transition-all duration-300"
              />
            </div>
            <div className="transition-all duration-300 hover:scale-105">
              <label htmlFor="excludeUsers" className="mr-2 text-yellow-400">排除用户:</label>
              <input
                type="text"
                id="excludeUsers"
                value={excludeUsers}
                onChange={(e) => setExcludeUsers(e.target.value)}
                placeholder="用户名，多个用逗号分隔"
                className="p-2 bg-black/50 text-yellow-400 border border-yellow-400/30 rounded focus:outline-none focus:ring-2 focus:ring-yellow-500 transition-all duration-300 w-64"
              />
            </div>
            <button
              onClick={() => fetchData()}
              className="px-6 py-2 bg-yellow-500 text-black rounded hover:bg-yellow-400 transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-yellow-500 font-medium"
            >
              刷新数据
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded text-red-400">
              {error}
            </div>
          )}

          {!loading && !error && (
            <div className="space-y-6 mt-8">
              {/* 第一行：每日访问趋势和用户增长趋势 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-black/50 p-6 rounded-lg border border-yellow-400/30 transition-all duration-300 hover:border-yellow-400/50">
                  <h2 className="text-xl font-semibold mb-4 text-yellow-400">每日访问趋势</h2>
                  <Line data={dailyStatsChartData} options={chartOptions} />
                </div>
                <div className="bg-black/50 p-6 rounded-lg border border-yellow-400/30 transition-all duration-300 hover:border-yellow-400/50">
                  <h2 className="text-xl font-semibold mb-4 text-yellow-400">用户增长趋势</h2>
                  <Line data={userGrowthChartData} options={chartOptions} />
                </div>
              </div>

              {/* 第二行：产品访问分布 */}
              <div className="bg-black/50 p-6 rounded-lg border border-yellow-400/30 transition-all duration-300 hover:border-yellow-400/50">
                <h2 className="text-xl font-semibold mb-4 text-yellow-400">产品访问分布</h2>
                <Line 
                  data={productDailyChartData} 
                  options={{
                    ...chartOptions,
                    onClick: (event, elements) => {
                      if (elements.length > 0) {
                        const datasetIndex = elements[0].datasetIndex;
                        const newDatasets = productDailyChartData.datasets.filter((_, index) => index === datasetIndex);
                        setProductDailyStats(prev => {
                          const selectedProduct = productDailyChartData.datasets[datasetIndex].label;
                          return prev.filter(stat => stat.product === selectedProduct);
                        });
                      } else {
                        fetchData(); // 重置为显示所有数据
                      }
                    }
                  }} 
                />
              </div>

              {/* 第三行：用户每日访问详情 */}
              <div className="bg-black/50 p-6 rounded-lg border border-yellow-400/30 transition-all duration-300 hover:border-yellow-400/50">
                <h2 className="text-xl font-semibold mb-4 text-yellow-400">用户每日访问详情</h2>
                <Line 
                  data={userDailyChartData} 
                  options={{
                    ...chartOptions,
                    onClick: (event, elements) => {
                      if (elements.length > 0) {
                        const datasetIndex = elements[0].datasetIndex;
                        const newDatasets = userDailyChartData.datasets.filter((_, index) => index === datasetIndex);
                        setUserDailyStats(prev => {
                          const selectedUser = userDailyChartData.datasets[datasetIndex].label;
                          return prev.filter(stat => stat.name === selectedUser);
                        });
                      } else {
                        fetchData(); // 重置为显示所有数据
                      }
                    }
                  }} 
                />
              </div>

              {/* 第四行：用户访问统计 */}
              <div className="bg-black/50 p-6 rounded-lg border border-yellow-400/30 transition-all duration-300 hover:border-yellow-400/50">
                <h2 className="text-xl font-semibold mb-4 text-yellow-400">用户访问统计</h2>
                <Bar data={userChartData} options={chartOptions} />
              </div>
            </div>
          )}

          {!loading && !error && userStats.length === 0 && (
            <div className="mt-8 text-center text-yellow-400/70">
              暂无数据
            </div>
          )}
        </div>
      </div>
    </div>
  );
}