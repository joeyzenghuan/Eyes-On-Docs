'use client';

import { signIn } from 'next-auth/react';
import { Button } from '@/components/ui/button';

export default function SignIn() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm space-y-4 rounded-lg border p-6 shadow-lg">
        <h2 className="text-center text-2xl font-bold">登录</h2>
        <Button
          className="w-full"
          onClick={() => signIn('github', { callbackUrl: '/' })}
        >
          使用GitHub登录
        </Button>
      </div>
    </div>
  );
}