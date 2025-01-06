import { NextResponse } from 'next/server';
import { CosmosClient } from '@azure/cosmos';
import { ClientSecretCredential } from '@azure/identity';
import * as fs from 'fs';
import * as path from 'path';

// Function to log to file
function logToFile(message: string, level: 'info' | 'error' | 'warning' | 'debug' = 'info') {
  const logLevel = process.env.LOG_LEVEL || 'info';
  const levels = ['debug', 'info', 'warning', 'error'];
  const currentLevelIndex = levels.indexOf(logLevel);
  const messageLevelIndex = levels.indexOf(level);

  if (messageLevelIndex < currentLevelIndex) {
    return;
  }
  const logDir = path.join(process.cwd(), 'logs');
  
  // Create logs directory if it doesn't exist
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir);
  }

  const logFile = path.join(logDir, `updates_${new Date().toISOString().split('T')[0]}.log`);
  
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}\n`;
  
  fs.appendFileSync(logFile, logMessage);
}

// Validate environment variables before initialization
const requiredEnvVars = [
  'APP_TENANT_ID',
  'APP_CLIENT_ID',
  'APP_CLIENT_SECRET',
  'AZURE_COSMOSDB_ACCOUNT',
  'AZURE_COSMOSDB_DATABASE',
  'AZURE_COSMOSDB_CONVERSATIONS_CONTAINER'
];

const missingEnvVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingEnvVars.length > 0) {
  const errorMessage = `Missing required environment variables: ${missingEnvVars.join(', ')}`;
  logToFile(errorMessage, 'error');
  throw new Error(errorMessage);
}


// Initialize Azure AD credentials
const credential = new ClientSecretCredential(
  process.env.APP_TENANT_ID!,
  process.env.APP_CLIENT_ID!,
  process.env.APP_CLIENT_SECRET! 
);


// Initialize the Cosmos Client with error handling
let client: CosmosClient;
try {
  client = new CosmosClient({
    endpoint: `https://${process.env.AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/`,
    aadCredentials: credential
  });

  const database = client.database(process.env.AZURE_COSMOSDB_DATABASE!);
  const container = database.container(process.env.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER!);

  // Log successful Cosmos Client connection
  logToFile(`Cosmos Client connected successfully to database: ${process.env.AZURE_COSMOSDB_DATABASE}, container: ${process.env.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER}`, 'info');
} catch (error) {
  const errorMessage = `Failed to initialize Cosmos Client: ${error instanceof Error ? error.message : String(error)}`;
  logToFile(errorMessage, 'error');
  throw error;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  logToFile(request.url, 'info');
  const product = searchParams.get('product');
  const language = searchParams.get('language');
  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20; // 每页20个
  const offset = (page - 1) * pageSize; // 计算偏移量
  const updateType = searchParams.get('updateType') || 'single'; // 新增 updateType 参数，默认为 single

  logToFile(`Received request with params: product=${product}, language=${language}, page=${page}, updateType=${updateType}`, 'info');

  try {
    let parameters = [];
    let conditions = [];
    let queryText = "";

    logToFile('Initial query text: ' + queryText, 'debug');

    // Default to first product if not specified
    const defaultProduct = 'AOAI-V2';
    const defaultLanguage = 'Chinese';

    if (product) {
      conditions.push("c.topic = @product");
      parameters.push({ name: '@product', value: product });
      logToFile(`Added product filter: ${product}`, 'debug');
    } else {
      conditions.push("c.topic = @product");
      parameters.push({ name: '@product', value: defaultProduct });
      logToFile(`Added default product filter: ${defaultProduct}`, 'debug');
    }

    if (language) {
      conditions.push("c.language = @language");
      parameters.push({ name: '@language', value: language });
      logToFile(`Added language filter: ${language}`, 'debug');
    } else {
      conditions.push("c.language = @language");
      parameters.push({ name: '@language', value: defaultLanguage });
      logToFile(`Added default language filter: ${defaultLanguage}`, 'debug');
    }

    // 根据 updateType 调整查询条件
    const query = updateType === 'weekly' 
      ? 'SELECT * FROM c WHERE IS_DEFINED(c.gpt_weekly_summary_tokens) AND c.topic = @product AND c.language = @language'
      : 'SELECT * FROM c WHERE IS_DEFINED(c.gpt_title_response) AND c.status != "skip" AND NOT IS_DEFINED(c.gpt_weekly_summary_tokens) AND c.topic = @product AND c.language = @language';

    queryText = query;
    logToFile('Updated query text with conditions: ' + queryText, 'debug');

    // 添加排序和分页
    queryText += " ORDER BY c.commit_time DESC OFFSET @offset LIMIT @limit";
    parameters.push(
      { name: '@offset', value: offset },
      { name: '@limit', value: pageSize }
    );
    logToFile(`Added sorting, offset, and limit: offset=${offset}, limit=${pageSize}`, 'debug');

    logToFile('Final query parameters: ' + JSON.stringify(parameters), 'info');

    const { resources: updates } = await client.database(process.env.AZURE_COSMOSDB_DATABASE!).container(process.env.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER!).items
      .query({ query: queryText, parameters })
      .fetchAll();

    logToFile(`Fetched ${updates.length} updates`, 'info');

    // 转换数据
    const transformedUpdates = updates
      .filter(update => {
        // 对于周总结，检查 teams_message_jsondata
        if (updateType === 'weekly') {
          return update.teams_message_jsondata && 
                 update.teams_message_jsondata.title && 
                 update.teams_message_jsondata.text;
        }
        // 对于单个更新，保持原有逻辑
        return update.gpt_title_response && !update.gpt_title_response.startsWith('0');
      })
      .map(update => {
        let tag = '';
        let title = '';
        let gptSummary = '';

        if (updateType === 'weekly') {
          // 从 teams_message_jsondata 提取信息
          const teamsData = update.teams_message_jsondata;
          title = teamsData.title.replace(/\[Weekly Summary\]\s*/g, '').trim();
          gptSummary = teamsData.text;

          // 尝试从标题中提取标签
          const tagMatch = title.match(/^\[(.*?)\]/);
          if (tagMatch) {
            tag = tagMatch[1].trim();
          }
        } else {
          // 单个更新的原有逻辑  其实不用在前端处理 0,1, 后端已经处理好了，放在 teams_message_jsondata.title中了
          // 后端已经处理好了 teams_message_jsondata.text =  commit_time +   gpt_summary_response（这里没用）
          const extractTagAndTitle = (titleResponse: string) => {
            const titleWithoutNumber = titleResponse.replace(/^\d+\s*/, '');
            const tagMatch = titleWithoutNumber.match(/^\[(.*?)\]\s*(.+)$/);
            
            if (tagMatch) {
              return {
                tag: tagMatch[1].trim(),
                title: tagMatch[2].trim()
              };
            }
            
            return {
              tag: '',
              title: titleWithoutNumber.trim()
            };
          };

          const { tag: extractedTag, title: extractedTitle } = extractTagAndTitle(update.gpt_title_response);
          tag = extractedTag;
          title = extractedTitle;
          gptSummary = update.gpt_summary_response;
        }

        logToFile('Individual update fields: ' + JSON.stringify({
          id: update.id,
          tag: tag,
          title: title,
          gptSummary: gptSummary
        }), 'debug');

        return {
          id: update.id,
          tag: tag,
          title: title,
          gptSummary: gptSummary,
          timestamp: update.commit_time,
          commitUrl: update.commit_url
        };
      });

        logToFile(`Transformed ${transformedUpdates.length} updates`, 'info');

    // 获取总数的查询条件
    const getCountCondition = (updateType: string) => {
      switch (updateType) {
        case 'weekly':
          return 'IS_DEFINED(c.gpt_weekly_summary_tokens)';
        case 'single':
        default:
          return 'IS_DEFINED(c.gpt_title_response) AND c.status != "skip" AND NOT IS_DEFINED(c.gpt_weekly_summary_tokens)';
      }
    };

    // 获取总数
    const countQuery = {
      query: `SELECT VALUE COUNT(1) FROM c WHERE ${getCountCondition(updateType)} AND c.topic = @product AND c.language = @language`,
      parameters: parameters.filter(p => !['@offset', '@limit'].includes(p.name))
    };
    logToFile('Count query: ' + JSON.stringify(countQuery), 'debug');

    const { resources: [totalCount] } = await client.database(process.env.AZURE_COSMOSDB_DATABASE!).container(process.env.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER!).items.query(countQuery).fetchAll();
    logToFile(`Total count of updates: ${totalCount}`, 'info');

    // 计算总页数
    const totalPages = Math.ceil(totalCount / pageSize);

    const response = {
      updates: transformedUpdates,
      pagination: {
        currentPage: page,
        totalPages: totalPages,
        totalItems: totalCount,
        pageSize: pageSize
      }
    };

    logToFile('Final response: ' + JSON.stringify(response, null, 2), 'debug');

    return NextResponse.json(response);
  } catch (error) {
    logToFile('Error in GET function: ' + error.message, 'error');
    return NextResponse.json(
      { error: 'Failed to fetch updates', details: error.message },
      { status: 500 }
    );
  }
}
