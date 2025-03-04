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

export default function UsagePage() {
  const [userStats, setUserStats] = useState<UsageStats[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [userGrowthStats, setUserGrowthStats] = useState<UserGrowthStats[]>([]);
  const [productDailyStats, setProductDailyStats] = useState<ProductDailyStats[]>([]);
  const [userDailyStats, setUserDailyStats] = useState<UserDailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 用户访问统计图表数据
  const userChartData = {
    labels: userStats.map(stat => stat.name || '匿名用户'),
    datasets: [
      {
        label: '访问次数',
        data: userStats.map(stat => stat.recordCount),
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        borderColor: 'rgb(75, 192, 192)',
        borderWidth: 1
      }
    ]
  };

  // 用户增长趋势图表数据
  const userGrowthChartData = {
    labels: userGrowthStats.map(stat => stat.date),
    datasets: [
      {
        label: '累计用户数',
        data: userGrowthStats.map(stat => stat.totalUsers),
        borderColor: 'rgb(147, 51, 234)',
        backgroundColor: 'rgba(147, 51, 234, 0.5)',
        tension: 0.1
      }
    ]
  };

  // 每日访问趋势图表数据
  const dailyChartData = {
    labels: dailyStats.map(stat => stat.date),
    datasets: [
      {
        label: '每日访问量',
        data: dailyStats.map(stat => stat.count),
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
        tension: 0.1
      }
    ]
  };

  // 图表通用选项
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  // 产品每日访问统计图表数据
  const productDailyChartData = {
    labels: [...new Set(productDailyStats.map(stat => stat.date))].sort(),
    datasets: [...new Set(productDailyStats.map(stat => stat.product))].map((product, index) => {
      const colors = [
        { bg: 'rgba(255, 99, 132, 0.5)', border: 'rgb(255, 99, 132)' },
        { bg: 'rgba(54, 162, 235, 0.5)', border: 'rgb(54, 162, 235)' },
        { bg: 'rgba(255, 206, 86, 0.5)', border: 'rgb(255, 206, 86)' },
        { bg: 'rgba(75, 192, 192, 0.5)', border: 'rgb(75, 192, 192)' },
        { bg: 'rgba(153, 102, 255, 0.5)', border: 'rgb(153, 102, 255)' },
        { bg: 'rgba(255, 159, 64, 0.5)', border: 'rgb(255, 159, 64)' },
        { bg: 'rgba(199, 199, 199, 0.5)', border: 'rgb(199, 199, 199)' },
        { bg: 'rgba(83, 102, 255, 0.5)', border: 'rgb(83, 102, 255)' },
        { bg: 'rgba(255, 99, 255, 0.5)', border: 'rgb(255, 99, 255)' },
        { bg: 'rgba(99, 255, 132, 0.5)', border: 'rgb(99, 255, 132)' },
        { bg: 'rgba(255, 159, 255, 0.5)', border: 'rgb(255, 159, 255)' },
        { bg: 'rgba(255, 206, 159, 0.5)', border: 'rgb(255, 206, 159)' },
      ];
      const colorIndex = index % colors.length;
      const dates = [...new Set(productDailyStats.map(stat => stat.date))].sort();
      return {
        label: product,
        data: dates.map(date => {
          const stat = productDailyStats.find(s => s.date === date && s.product === product);
          return stat ? stat.count : 0;
        }),
        backgroundColor: colors[colorIndex].bg,
        borderColor: colors[colorIndex].border,
        borderWidth: 1
      };
    })
  };

  // 用户每日访问统计图表数据
  const userDailyChartData = {
    labels: [...new Set(userDailyStats.map(stat => stat.date))].sort(),
    datasets: [...new Set(userDailyStats.map(stat => stat.name))].map((name, index) => {
      const colors = [
        { bg: 'rgba(255, 99, 132, 0.5)', border: 'rgb(255, 99, 132)' },
        { bg: 'rgba(54, 162, 235, 0.5)', border: 'rgb(54, 162, 235)' },
        { bg: 'rgba(255, 206, 86, 0.5)', border: 'rgb(255, 206, 86)' },
        { bg: 'rgba(75, 192, 192, 0.5)', border: 'rgb(75, 192, 192)' },
        { bg: 'rgba(153, 102, 255, 0.5)', border: 'rgb(153, 102, 255)' },
        { bg: 'rgba(255, 159, 64, 0.5)', border: 'rgb(255, 159, 64)' },
        { bg: 'rgba(199, 199, 199, 0.5)', border: 'rgb(199, 199, 199)' },
        { bg: 'rgba(83, 102, 255, 0.5)', border: 'rgb(83, 102, 255)' },
        { bg: 'rgba(255, 99, 255, 0.5)', border: 'rgb(255, 99, 255)' },
        { bg: 'rgba(99, 255, 132, 0.5)', border: 'rgb(99, 255, 132)' },
        { bg: 'rgba(255, 159, 255, 0.5)', border: 'rgb(255, 159, 255)' },
        { bg: 'rgba(255, 206, 159, 0.5)', border: 'rgb(255, 206, 159)' },
      ];
      const colorIndex = index % colors.length;
      const dates = [...new Set(userDailyStats.map(stat => stat.date))].sort();
      return {
        label: name,
        data: dates.map(date => {
          const stat = userDailyStats.find(s => s.date === date && s.name === name);
          return stat ? stat.count : 0;
        }),
        backgroundColor: colors[colorIndex].bg,
        borderColor: colors[colorIndex].border,
        borderWidth: 1
      };
    })
  };

  // 堆叠图表选项
  const stackedChartOptions = {
    ...chartOptions,
    scales: {
      x: {
        stacked: true
      },
      y: {
        stacked: true,
        beginAtZero: true
      }
    }
  };

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/usage');
        if (!response.ok) {
          throw new Error('Failed to fetch usage statistics');
        }
        const data = await response.json();
        setUserStats(data.userStats);
        setDailyStats(data.dailyStats);
        setUserGrowthStats(data.userGrowthStats || []);
        setProductDailyStats(data.productDailyStats || []);
        setUserDailyStats(data.userDailyStats || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background-primary p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold mb-6 text-text-primary">用户访问统计</h1>
          <div className="text-text-secondary">加载中...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background-primary p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold mb-6 text-text-primary">用户访问统计</h1>
          <div className="text-red-500">错误: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background-primary p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-text-primary">用户访问统计</h1>
        
        <div className="grid grid-cols-1 gap-8 mb-8">
          {/* 每日访问趋势图表 */}
          <div className="bg-background-secondary rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-text-primary">每日访问趋势</h2>
            <Line data={dailyChartData} options={chartOptions} />
          </div>

          {/* 产品每日访问统计图表 */}
          <div className="bg-background-secondary rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-text-primary">产品每日访问统计</h2>
            <Bar data={productDailyChartData} options={stackedChartOptions} />
          </div>

          {/* 用户每日访问统计图表 */}
          <div className="bg-background-secondary rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-text-primary">用户每日访问统计</h2>
            <Bar data={userDailyChartData} options={stackedChartOptions} />
          </div>

          {/* 用户访问统计图表 */}
          <div className="bg-background-secondary rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-text-primary">用户访问分布</h2>
            <Bar data={userChartData} options={chartOptions} />
          </div>

          {/* 用户增长趋势图表 */}
          <div className="bg-background-secondary rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-text-primary">用户增长趋势</h2>
            <Line data={userGrowthChartData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}