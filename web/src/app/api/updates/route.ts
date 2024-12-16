import { NextResponse } from 'next/server';
import { CosmosClient } from '@azure/cosmos';
import { ClientSecretCredential } from '@azure/identity';
import * as fs from 'fs';
import * as path from 'path';

// Function to log to file
function logToFile(message: string) {
  const logDir = path.join(process.cwd(), 'logs');
  
  // Create logs directory if it doesn't exist
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir);
  }

  const logFile = path.join(logDir, `updates_${new Date().toISOString().split('T')[0]}.log`);
  
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  
  fs.appendFileSync(logFile, logMessage);
}

// Initialize Azure AD credentials
const credential = new ClientSecretCredential(
  process.env.APP_TENANT_ID || '',
  process.env.APP_CLIENT_ID || '',
  process.env.APP_CLIENT_SECRET || ''
);

// Initialize the Cosmos Client
const client = new CosmosClient({
  endpoint: `https://${process.env.AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/`,
  aadCredentials: credential
});

const database = client.database(process.env.AZURE_COSMOSDB_DATABASE || '');
const container = database.container(process.env.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER || '');

// Log successful Cosmos Client connection
logToFile(`Cosmos Client connected successfully to database: ${process.env.AZURE_COSMOSDB_DATABASE}, container: ${process.env.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER}`);

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const product = searchParams.get('product');
  const language = searchParams.get('language');
  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 10; // 每页10个
  const offset = (page - 1) * pageSize; // 计算偏移量

  logToFile(`Received request with params: product=${product}, language=${language}, page=${page}`);

  try {
    let parameters = [];
    let conditions = [];
    let queryText = "SELECT * FROM c WHERE IS_DEFINED(c.gpt_title_response)";

    logToFile('Initial query text: ' + queryText);

    // Default to first product if not specified
    const defaultProduct = 'AOAI-V2';
    const defaultLanguage = 'Chinese';

    if (product) {
      conditions.push("c.topic = @product");
      parameters.push({ name: '@product', value: product });
      logToFile(`Added product filter: ${product}`);
    } else {
      conditions.push("c.topic = @product");
      parameters.push({ name: '@product', value: defaultProduct });
      logToFile(`Added default product filter: ${defaultProduct}`);
    }

    if (language) {
      conditions.push("c.language = @language");
      parameters.push({ name: '@language', value: language });
      logToFile(`Added language filter: ${language}`);
    } else {
      conditions.push("c.language = @language");
      parameters.push({ name: '@language', value: defaultLanguage });
      logToFile(`Added default language filter: ${defaultLanguage}`);
    }

    if (conditions.length > 0) {
      queryText += " AND " + conditions.join(" AND ");
      logToFile('Updated query text with conditions: ' + queryText);
    }

    // 添加排序和分页
    queryText += " ORDER BY c.commit_time DESC OFFSET @offset LIMIT @limit";
    parameters.push(
      { name: '@offset', value: offset },
      { name: '@limit', value: pageSize }
    );
    logToFile(`Added sorting, offset, and limit: offset=${offset}, limit=${pageSize}`);

    logToFile('Final query parameters: ' + JSON.stringify(parameters));

    const { resources: updates } = await container.items
      .query({ query: queryText, parameters })
      .fetchAll();

    logToFile(`Fetched ${updates.length} updates`);
    logToFile('Raw updates: ' + JSON.stringify(updates, null, 2));

    // 转换数据
    const transformedUpdates = updates.map(update => {
      logToFile('Individual update fields: ' + JSON.stringify({
        id: update.id,
        gpt_title_response: update.gpt_title_response,
        gpt_summary_response: update.gpt_summary_response
      }));

      return {
        id: update.id,
        title: update.gpt_title_response,
        gptSummary: update.gpt_summary_response,
        timestamp: update.commit_time,
        commitUrl: update.commit_url
      };
    });

    logToFile(`Transformed ${transformedUpdates.length} updates`);

    // 获取总数
    const countQuery = {
      query: `SELECT VALUE COUNT(1) FROM c WHERE IS_DEFINED(c.gpt_title_response)${conditions.length > 0 ? ' AND ' + conditions.join(" AND ") : ''}`,
      parameters: parameters.filter(p => !['@offset', '@limit'].includes(p.name))
    };
    logToFile('Count query: ' + JSON.stringify(countQuery));

    const { resources: [totalCount] } = await container.items.query(countQuery).fetchAll();
    logToFile(`Total count of updates: ${totalCount}`);

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

    logToFile('Final response: ' + JSON.stringify(response, null, 2));

    return NextResponse.json(response);
  } catch (error) {
    logToFile('Error in GET function: ' + error.message);
    return NextResponse.json(
      { error: 'Failed to fetch updates', details: error.message },
      { status: 500 }
    );
  }
}
