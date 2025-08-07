import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { logger } from "@/lib/logger";

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" }
      },
      async authorize(credentials) {
        logger.debug(`开始用户认证，用户名：${credentials?.username}`);
        
        if (!credentials?.username) {
          logger.warn("认证失败：用户名为空");
          return null;
        }
        
        logger.info(`认证成功，用户名：${credentials.username}`);
        return {
          id: credentials.username,
          name: credentials.username,
        };
      }
    }),
  ],
  callbacks: {
    session({ session, token }) {
      if (session?.user) {
        session.user.id = token.sub;
        logger.info(`更新session信息，用户ID：${token.sub}`);
      }
      return session;
    },
    redirect({ url, baseUrl }) {
      const redirectUrl = url.startsWith(baseUrl) ? url : baseUrl;
      logger.debug(`重定向请求，从 ${url} 到 ${redirectUrl}`);
      return redirectUrl;
    },
  },
});

export { handler as GET, handler as POST };