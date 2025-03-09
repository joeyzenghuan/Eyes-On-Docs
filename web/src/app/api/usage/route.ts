import { NextResponse } from 'next/server';
import { CosmosClient } from '@azure/cosmos';
import { ClientSecretCredential } from '@azure/identity';
import { logger } from '@/lib/logger';

// Initialize Azure AD credentials
const credential = new ClientSecretCredential(
  process.env.APP_TENANT_ID!,
  process.env.APP_CLIENT_ID!,
  process.env.APP_CLIENT_SECRET! 
);

// Initialize the Cosmos Client
const client = new CosmosClient({
  endpoint: `https://${process.env.AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/`,
  aadCredentials: credential
});

export async function GET() {
  logger.info('开始获取使用统计数据');
  try {
    const database = client.database(process.env.AZURE_COSMOSDB_DATABASE!);
    const container = database.container(process.env.AZURE_COSMOSDB_USER_TRAFFIC_CONTAINER!);

    // 获取每个用户的历史访问次数统计
    const userStatsQuery = {
      query: 'SELECT c.userInfo.name, COUNT(1) AS recordCount FROM c WHERE c.userInfo.name NOT LIKE \'anonymous\' AND c.path = "/" GROUP BY c.userInfo.name'
    };
    const { resources: userStats } = await container.items.query(userStatsQuery).fetchAll();

    // 获取每日访问统计
    const dailyStatsQuery = {
      query: 'SELECT SUBSTRING(c.timestamp, 0, 10) as date, COUNT(1) as count FROM c WHERE c.userInfo.name NOT LIKE \'anonymous\' AND c.path = "/" GROUP BY SUBSTRING(c.timestamp, 0, 10)'
    };
    const { resources: dailyStats } = await container.items.query(dailyStatsQuery).fetchAll();

    // 获取产品每日访问统计
    const productDailyStatsQuery = {
      query: 'SELECT SUBSTRING(c.timestamp, 0, 10) as date, c.searchParams.product, COUNT(1) as count FROM c WHERE c.userInfo.name NOT LIKE \'anonymous\' AND c.path = "/" GROUP BY SUBSTRING(c.timestamp, 0, 10), c.searchParams.product'
    };
    const { resources: productDailyStats } = await container.items.query(productDailyStatsQuery).fetchAll();

    // 获取用户每日访问统计
    const userDailyStatsQuery = {
      query: 'SELECT SUBSTRING(c.timestamp, 0, 10) as date, c.userInfo.name as name, COUNT(1) as count FROM c WHERE c.userInfo.name NOT LIKE \'anonymous\' AND c.path = "/" GROUP BY SUBSTRING(c.timestamp, 0, 10), c.userInfo.name'
    };
    const { resources: userDailyStats } = await container.items.query(userDailyStatsQuery).fetchAll();

    // 获取用户首次访问日期
    const firstVisitQuery = {
      query: 'SELECT c.userInfo.name, MIN(SUBSTRING(c.timestamp, 0, 10)) as firstVisitDate FROM c WHERE c.userInfo.name NOT LIKE \'anonymous\' AND c.path = "/" GROUP BY c.userInfo.name'
    };
    const { resources: firstVisitData } = await container.items.query(firstVisitQuery).fetchAll();

    // 按日期统计新增用户数
    const dailyNewUsers = firstVisitData.reduce((acc: { [key: string]: number }, curr) => {
      acc[curr.firstVisitDate] = (acc[curr.firstVisitDate] || 0) + 1;
      return acc;
    }, {});

    // 转换为数组格式并排序
    const sortedDailyData = Object.entries(dailyNewUsers)
      .map(([date, newUsers]) => ({ date, newUsers }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // 计算累计用户数
    const userGrowthStats = sortedDailyData.reduce((acc: any[], curr) => {
      const prevTotal = acc.length > 0 ? acc[acc.length - 1].totalUsers : 0;
      acc.push({
        date: curr.date,
        totalUsers: prevTotal + curr.newUsers
      });
      return acc;
    }, []);

    const response = {
      userStats: userStats.sort((a, b) => b.recordCount - a.recordCount),
      dailyStats: dailyStats.sort((a, b) => a.date.localeCompare(b.date)),
      userGrowthStats,
      productDailyStats: productDailyStats.sort((a, b) => a.date.localeCompare(b.date)),
      userDailyStats: userDailyStats.sort((a, b) => a.date.localeCompare(b.date))
    };

    logger.info(`使用统计数据获取成功，用户统计数: ${userStats.length}, 每日统计数: ${dailyStats.length}, 用户增长统计数: ${userGrowthStats.length}, 产品每日统计数: ${productDailyStats.length}, 用户每日统计数: ${userDailyStats.length}`);

    return NextResponse.json(response);
  } catch (error) {
    logger.error(`获取使用统计数据失败: ${error instanceof Error ? error.message : String(error)}${error instanceof Error && error.stack ? '\n' + error.stack : ''}`);
    return NextResponse.json(
      { error: 'Failed to fetch usage statistics', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}