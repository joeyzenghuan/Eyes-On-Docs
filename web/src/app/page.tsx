"use client";

import React from 'react';
import { useSearchParams } from 'next/navigation';
import Filters from '@/components/Filters';
import { Pagination } from '@/components/Pagination';
import UpdateCard from '@/components/UpdateCard';

async function getUpdates(product: string, language: string, page: number) {
  try {
    const response = await fetch(`/api/updates?product=${product}&language=${language}&page=${page}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch updates');
    }

    const data = await response.json();
    
    // Log the received data
    console.log('Received updates data:', JSON.stringify(data, null, 2));

    // Transform the API response to match the existing Update interface
    const transformedUpdates = data.updates.map((update: any) => {
      console.log('Transforming update:', JSON.stringify(update, null, 2));
      return {
        id: update.id,
        topic: update.product,
        language: update.language,
        title: update.title,
        timestamp: update.timestamp,
        commitUrl: update.commitUrl,
        gptSummary: update.gptSummary, // Explicitly pass gptSummary
        tag: update.tag // Add tag property
      };
    });

    return {
      updates: transformedUpdates,
      total: data.pagination.totalItems,
      page: data.pagination.currentPage,
      pageSize: 20
    };
  } catch (error) {
    console.error('Error fetching updates:', error);
    return {
      updates: [],
      total: 0,
      page: page,
      pageSize: 20
    };
  }
}

interface Update {
  id: string;
  topic: string;
  language: string;
  title: string;
  timestamp: string;
  commitUrl: string;
  gptSummary?: string;
  tag?: string; // Add tag property
}

export default function Home({ searchParams }: { searchParams: { product?: string; language?: string; page?: string } }) {
  const product = searchParams.product || 'AOAI-V2';
  const language = searchParams.language || 'Chinese';
  const page = parseInt(searchParams.page || '1', 10);

  const [updates, setUpdates] = React.useState<Update[]>([]);
  const [pagination, setPagination] = React.useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    pageSize: 20
  });
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    async function fetchUpdates() {
      setIsLoading(true);
      try {
        const data = await getUpdates(product, language, page);
        setUpdates(data.updates);
        setPagination({
          currentPage: data.page,
          totalPages: Math.ceil(data.total / 20),
          totalItems: data.total,
          pageSize: 20
        });
      } catch (error) {
        console.error('Failed to fetch updates:', error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchUpdates();
  }, [product, language, page]);

  return (
    <main className="flex min-h-screen flex-col p-24 bg-background-primary">
      <div className="max-w-5xl w-full mx-auto">
        <h1 className="text-8xl font-black mb-6 text-yellow-400 text-center 
          tracking-widest uppercase font-orbitron 
          transform hover:scale-105 transition-transform duration-300
          drop-shadow-[0_0_20px_rgba(255,255,0,0.6)]
          animate-[pulse_5s_ease-in-out_infinite]
          bg-clip-text text-transparent 
          bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600
          hover:bg-gradient-to-br
          border-b-4 border-yellow-600 pb-2
          hover:border-opacity-75 transition-all"
        >
          EYES ON DOCS
        </h1>
        
        <div className="w-full flex justify-start mb-6">
          <Filters 
            products={['AOAI-V2', 'AML']} 
            languages={['Chinese', 'English']}
          />
        </div>

        {isLoading ? (
          <div className="text-center text-accent-secondary animate-pulse">Loading...</div>
        ) : updates.length === 0 ? (
          <div className="text-center text-text-secondary">No updates found</div>
        ) : (
          <>
            <div className="mt-6 grid grid-cols-1 gap-4 w-full">
              {updates.map((update) => (
                <UpdateCard
                  key={update.id}
                  id={update.id}
                  title={update.title}
                  tag={update.tag}
                  timestamp={update.timestamp}
                  commitUrl={update.commitUrl}
                  gptSummary={update.gptSummary}
                />
              ))}
            </div>
            <div className="mt-8 flex justify-center">
              <Pagination 
                currentPage={pagination.currentPage} 
                totalPages={pagination.totalPages}
                totalItems={pagination.totalItems}
                pageSize={20}
                onPageChange={(newPage) => {
                  const params = new URLSearchParams(window.location.search);
                  params.set('page', newPage.toString());
                  window.location.search = params.toString();
                }}
              />
            </div>
          </>
        )}
      </div>
    </main>
  );
}
