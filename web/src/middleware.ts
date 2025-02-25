import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const session = request.cookies.get('next-auth.session-token');
  const isAuthPage = request.nextUrl.pathname.startsWith('/auth');

  if (!session && !isAuthPage) {
    return NextResponse.redirect(new URL('/auth', request.url));
  }

  if (session && isAuthPage) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};