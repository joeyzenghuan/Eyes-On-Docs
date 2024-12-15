"use client";

import React from 'react';
import { useSearchParams } from 'next/navigation';
import Filters from '@/components/Filters';
import { Pagination } from '@/components/Pagination';
import { UpdateCard } from '@/components/UpdateCard';

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
        summary: update.summary,
        commit_time: update.timestamp,
        url: update.commitUrl,
        author: '', // The API doesn't seem to return an author, so we'll leave it empty
        gptSummary: update.gptSummary // Explicitly pass gptSummary
      };
    });

    return {
      updates: transformedUpdates,
      total: data.pagination.totalItems,
      page: data.pagination.currentPage,
      pageSize: 10
    };
  } catch (error) {
    console.error('Error fetching updates:', error);
    return {
      updates: [],
      total: 0,
      page: page,
      pageSize: 10
    };
  }
}

interface Update {
  id: string;
  topic: string;
  language: string;
  title: string;
  summary: string;
  commit_time: string;
  url: string;
  author: string;
  gptSummary: string; // Make sure this is not optional
}

export default function Home({ searchParams }: { searchParams: { product?: string; language?: string; page?: string } }) {
  // Define unique products and languages for filtering
  const products = ['AOAI-V2', 'AML'];
  const languages = ['Chinese', 'English'];

  const product = searchParams.product || '';
  const language = searchParams.language || '';
  const page = parseInt(searchParams.page || '1');

  const [updates, setUpdates] = React.useState<Update[]>([]);
  const [total, setTotal] = React.useState(0);
  const [currentPage, setCurrentPage] = React.useState(page);

  React.useEffect(() => {
    async function fetchUpdates() {
      const { updates: fetchedUpdates, total: fetchedTotal, page: fetchedPage } = await getUpdates(product, language, page);
      setUpdates(fetchedUpdates as Update[]);
      setTotal(fetchedTotal);
      setCurrentPage(fetchedPage);
    }
    fetchUpdates();
  }, [product, language, page]);

  return (
    <main className="flex min-h-screen flex-col p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-6">Documentation Updates</h1>
        
        <Filters 
          products={products} 
          languages={languages}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4">
        {updates.map((update) => (
          <UpdateCard
            key={update.id}
            title={update.title}
            summary={update.summary}
            gptSummary={update.gptSummary}
            timestamp={update.commit_time}
            documentUrl={update.url}
            commitUrl={update.url}
            product={update.topic}
            language={update.language}
          />
        ))}
      </div>

      <Pagination
        currentPage={currentPage}
        totalPages={Math.ceil(total / 10)}
        onPageChange={(newPage) => {
          const params = new URLSearchParams(window.location.search);
          params.set('page', newPage.toString());
          window.location.search = params.toString();
        }}
      />
    </main>
  );
}
