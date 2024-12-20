"use client";

import React, { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Filters from '@/components/Filters';
import { Pagination } from '@/components/Pagination';
import UpdateCard from '@/components/UpdateCard';

async function getUpdates(product: string, language: string, page: number, updateType: 'single' | 'weekly') {
  try {
    const params = new URLSearchParams({
      product: product || 'AOAI-V2',
      language: language || 'Chinese',
      page: page.toString(),
      updateType: updateType
    });

    const response = await fetch(`/api/updates?${params}`, {
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
  const [updateType, setUpdateType] = useState<'single' | 'weekly'>('single');

  const toggleUpdateType = (type: 'single' | 'weekly') => {
    setUpdateType(type);
  };

  React.useEffect(() => {
    async function fetchUpdates() {
      setIsLoading(true);
      try {
        const data = await getUpdates(product, language, page, updateType);
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
  }, [product, language, page, updateType]);

  return (
    <main className="min-h-screen p-6 md:p-12 bg-background-primary text-text-primary">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-8xl font-black mb-6 text-yellow-400 text-center 
          transform 
          drop-shadow-[0_0_20px_rgba(255,255,0,0.6)]
          animate-[pulse_5s_ease-in-out_infinite]
          bg-clip-text text-transparent 
          bg-gradient-to-br from-yellow-400 to-yellow-600
          border-b-4 border-yellow-600 pb-2
          transition-all duration-300
          hover:scale-[1.02]
          hover:drop-shadow-[0_0_30px_rgba(255,255,0,0.8)]
        ">
          EYES ON DOCS
        </h1>

        <div className="flex justify-between items-center mb-4">
          <Filters 
            products={['AOAI-V2', 'AML']} 
            languages={['Chinese', 'English']}
          />
          <div className="flex items-center justify-end w-full">
            <div 
              className="
                relative flex w-72 bg-background-secondary rounded-full p-1 cursor-pointer
                transition-all duration-300
                hover:scale-[1.02]
                hover:shadow-md
              "
              onClick={() => toggleUpdateType(updateType === 'single' ? 'weekly' : 'single')}
            >
              {/* 滑动背景 */}
              <div 
                className={`
                  absolute top-1 bottom-1 w-1/2 bg-accent-secondary rounded-full 
                  transition-all duration-300 ease-in-out
                  ${updateType === 'single' ? 'left-1' : 'left-1/2'}
                  shadow-md
                `}
              />
              
              {/* 文字按钮 */}
              <div className="flex w-full z-10">
                <div 
                  className={`
                    w-1/2 text-center py-2 rounded-full 
                    transition-colors duration-300
                    ${updateType === 'single' ? 'text-background-primary' : 'text-text-secondary hover:text-accent-secondary'}
                  `}
                >
                  Single Update
                </div>
                <div 
                  className={`
                    w-1/2 text-center py-2 rounded-full 
                    transition-colors duration-300
                    ${updateType === 'weekly' ? 'text-background-primary' : 'text-text-secondary hover:text-accent-secondary'}
                  `}
                >
                  Weekly Summary
                </div>
              </div>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center text-text-secondary">Loading...</div>
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
      {/* 作者信息 */}
      <footer className="mt-12 text-center text-text-secondary text-sm">
        <div className="border-t border-accent-secondary/30 pt-6">
          <p>
            🚀 Created by <span className="font-bold text-accent-secondary">Joey Zeng</span> • 
            <a 
              href="mailto:zehua@microsoft.com" 
              className="
                ml-2
                hover:text-accent-secondary 
                transition-colors 
                duration-300 
                underline
                hover:no-underline
              "
            >
              zehua@microsoft.com
            </a>
          </p>
        </div>
      </footer>
    </main>
  );
}
