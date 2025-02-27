'use client';

import { signIn } from 'next-auth/react';
import { useState } from 'react';

export default function AuthPage() {
  const [username, setUsername] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    signIn('credentials', { 
      username,
      callbackUrl: '/' 
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-8xl w-full space-y-8 relative">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 blur-3xl" />
        <div className="relative">
          <h2 className="mt-6 text-center text-8xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400 animate-pulse whitespace-nowrap">
            Welcome to Eyes On Docs
          </h2>
        </div>
        <div className="mt-8 relative flex flex-col items-center justify-center space-y-4">
          <form onSubmit={handleLogin} className="w-full max-w-sm">
            <div className="flex flex-col space-y-4">
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your name"
                required
                className="px-4 py-2 rounded-lg text-black
                  bg-white/90 backdrop-blur-sm
                  border border-purple-400/30
                  focus:outline-none focus:ring-2 focus:ring-purple-500
                  transition-all duration-300"
              />
              <button
                type="submit"
                className="group py-2 px-6 text-sm font-medium rounded-lg text-white
                  bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500
                  transition-all duration-300 ease-in-out
                  shadow-[0_0_15px_rgba(139,92,246,0.5)]
                  hover:shadow-[0_0_30px_rgba(139,92,246,0.8)]
                  focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                Let's Go
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}