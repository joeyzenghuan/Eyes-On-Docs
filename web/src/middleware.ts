import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';
import { CosmosClient } from '@azure/cosmos';
import { ClientSecretCredential } from '@azure/identity';

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

export async function middleware(request: NextRequest) {
  // 获取用户会话信息
  const token = await getToken({ req: request as any });
  const isAuthPage = request.nextUrl.pathname.startsWith('/auth');

  // 记录访问信息
  const url = new URL(request.url);
  const visitInfo = {
    timestamp: new Date().toISOString(),
    path: url.pathname,
    searchParams: {
      product: url.searchParams.get('product') || 'AOAI-V2',
      language: url.searchParams.get('language') || 'Chinese',
      page: url.searchParams.get('page') || '1',
      updateType: url.searchParams.get('updateType') || 'single'
    },
    userInfo: {
      id: token?.sub || 'anonymous',
      emial: token?.email || null,
      name: token?.name || 'anonymous',
      image: token?.picture || null
    }
  };

  // 设置window.userId用于GA4跟踪
  const response = NextResponse.next();
  response.headers.set('Set-Cookie', `github_user_id=${token?.sub || 'anonymous'}; Path=/; SameSite=Strict`);

  //console.log
  console.log('visitInfo:', visitInfo);

  // 将访问信息写入Cosmos DB
  try {
    await client
      .database(process.env.AZURE_COSMOSDB_DATABASE!)
      .container(process.env.AZURE_COSMOSDB_USER_TRAFFIC_CONTAINER!)
      .items.create(visitInfo);
  } catch (error) {
    console.error('Failed to log visit info to Cosmos DB:', error);
  }

  // 身份验证逻辑
  if (!token && !isAuthPage) {
    return NextResponse.redirect(new URL('/auth', request.url));
  }

  if (token && isAuthPage) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return response;
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};