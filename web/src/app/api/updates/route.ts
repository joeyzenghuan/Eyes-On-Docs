import { NextResponse } from 'next/server';
import { CosmosClient } from '@azure/cosmos';
import { ClientSecretCredential } from '@azure/identity';

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
console.log(`Cosmos Client connected successfully to database: ${process.env.AZURE_COSMOSDB_DATABASE}, container: ${process.env.AZURE_COSMOSDB_CONVERSATIONS_CONTAINER}`);

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const product = searchParams.get('product');
  const language = searchParams.get('language');
  const limit = 5; // Limit to 5 latest results

  console.log(`Received request with params: product=${product}, language=${language}`);

  try {
    let parameters = [];
    let conditions = [];
    let queryText = "SELECT * FROM c";

    console.log('Initial query text:', queryText);

    if (product) {
      conditions.push("c.topic = @product");
      parameters.push({ name: '@product', value: product });
      console.log(`Added product filter: ${product}`);
    }

    if (language) {
      conditions.push("c.language = @language");
      parameters.push({ name: '@language', value: language });
      console.log(`Added language filter: ${language}`);
    }

    if (conditions.length > 0) {
      queryText += " WHERE " + conditions.join(" AND ");
      console.log('Updated query text with conditions:', queryText);
    }

    // Add sorting by commit time in descending order and limit to 5 results
    queryText += " ORDER BY c.commit_time DESC OFFSET 0 LIMIT @limit";
    parameters.push({ name: '@limit', value: limit });
    console.log(`Added sorting and limit: ${limit} results`);

    console.log('Final query parameters:', parameters);

    const { resources: updates } = await container.items
      .query({ query: queryText, parameters })
      .fetchAll();

    console.log(`Fetched ${updates.length} updates`);

    console.log('Raw updates:', JSON.stringify(updates, null, 2));

    // Transform the data to match the front-end requirements
    const transformedUpdates = updates.map(update => {
      console.log('Individual update fields:', {
        id: update.id,
        gpt_title_response: update.gpt_title_response,
        summary: update.summary,
        commit_message: update.commit_message,
        gpt_summary_response: update.gpt_summary_response
      });

      return {
        id: update.id,
        title: update.gpt_title_response || 'Document Update',
        summary: update.summary || update.commit_message,
        gptSummary: update.gpt_summary_response || '', // Explicitly use gpt_summary_response
        timestamp: update.commit_time,
        documentUrl: update.document_url || update.html_url,
        commitUrl: update.commit_url || update.html_url,
        product: update.topic,
        language: update.language
      };
    });

    console.log(`Transformed ${transformedUpdates.length} updates`);

    // Get total count for all matching updates
    const countQuery = {
      query: `SELECT VALUE COUNT(1) FROM c${conditions.length > 0 ? ' WHERE ' + conditions.join(" AND ") : ''}`,
      parameters: parameters.filter(p => p.name !== '@limit')
    };
    console.log('Count query:', countQuery);

    const { resources: [totalCount] } = await container.items.query(countQuery).fetchAll();
    console.log(`Total count of updates: ${totalCount}`);

    const response = {
      updates: transformedUpdates,
      pagination: {
        currentPage: 1,
        totalPages: 1,
        totalItems: totalCount
      }
    };

    console.log('Final response:', JSON.stringify(response, null, 2));

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error in GET function:', error);
    return NextResponse.json(
      { error: 'Failed to fetch updates', details: error.message },
      { status: 500 }
    );
  }
}
