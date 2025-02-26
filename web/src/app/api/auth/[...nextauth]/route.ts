import NextAuth from "next-auth";
import GithubProvider from "next-auth/providers/github";

const handler = NextAuth({
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_ID || "",
      clientSecret: process.env.GITHUB_SECRET || "",
    }),
  ],
  callbacks: {
    session({ session, token }) {
      if (session?.user) {
        session.user.id = token.sub;
      }
      return session;
    },
    redirect({ url, baseUrl }) {
      // 如果URL以baseUrl开头，说明是内部重定向，允许重定向
      if (url.startsWith(baseUrl)) return url;
      // 否则重定向到主页
      return baseUrl;
    },
  },
});

export { handler as GET, handler as POST };