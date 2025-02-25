"use client";

import React, { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface FiltersProps {
  products: string[];
  languages: string[];
}

export default function Filters({ products, languages }: FiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [selectedProduct, setSelectedProduct] = useState(searchParams.get('product') || products[0]);
  const [selectedLanguage, setSelectedLanguage] = useState(searchParams.get('language') || languages[0]);

  const handleProductChange = (product: string) => {
    const params = new URLSearchParams(searchParams);
    params.set('product', product);
    params.set('page', '1');
    router.push(`/?${params.toString()}`);
    setSelectedProduct(product);
  };

  const handleLanguageChange = (language: string) => {
    const params = new URLSearchParams(searchParams);
    params.set('language', language);
    params.set('page', '1');
    router.push(`/?${params.toString()}`);
    setSelectedLanguage(language);
  };

  return (
    <div className="flex items-center space-x-4">
      {/* Product Filter */}
      <div className="relative group">
        <select 
          value={selectedProduct} 
          onChange={(e) => handleProductChange(e.target.value)}
          className="
            appearance-none 
            w-48 
            bg-background-primary 
            border-4 border-transparent
            text-text-secondary 
            py-2 
            px-3 
            pr-8 
            cursor-pointer 
            focus:outline-none 
            focus:ring-2 
            focus:ring-accent-secondary 
            transition-all 
            duration-300
            truncate
            tracking-wider
            font-mono
            uppercase
            relative
            before:absolute 
            before:inset-0 
            before:border-4 
            before:border-yellow-100 
            before:pointer-events-none
            before:transition-all 
            before:duration-300
            hover:before:border-yellow-500/50
            hover:text-accent-secondary
            hover:bg-accent-secondary/10
          "
        >
          {products.map(product => (
            <option key={product} value={product} className="bg-background-primary text-text-secondary">
              {product}
            </option>
          ))}
        </select>
        <div className="
          pointer-events-none 
          absolute 
          inset-y-0 
          right-0 
          flex 
          items-center 
          px-2 
          text-text-secondary
          group-hover:text-accent-secondary
          transition-colors
          duration-300
        ">
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-4 w-4" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M19 9l-7 7-7-7" 
            />
          </svg>
        </div>
      </div>

      {/* Language Filter */}
      <div className="relative group">
        <select 
          value={selectedLanguage} 
          onChange={(e) => handleLanguageChange(e.target.value)}
          className="
            appearance-none 
            w-48 
            bg-background-primary 
            border-4 border-transparent
            text-text-secondary 
            py-2 
            px-3 
            pr-8 
            cursor-pointer 
            focus:outline-none 
            focus:ring-2 
            focus:ring-accent-secondary 
            transition-all 
            duration-300
            truncate
            tracking-wider
            font-mono
            uppercase
            relative
            before:absolute 
            before:inset-0 
            before:border-4 
            before:border-yellow-100 
            before:pointer-events-none
            before:transition-all 
            before:duration-300
            hover:before:border-yellow-500/50
            hover:text-accent-secondary
            hover:bg-accent-secondary/10
          "
        >
          {languages.map(language => (
            <option key={language} value={language} className="bg-background-primary text-text-secondary">
              {language}
            </option>
          ))}
        </select>
        <div className="
          pointer-events-none 
          absolute 
          inset-y-0 
          right-0 
          flex 
          items-center 
          px-2 
          text-text-secondary
          group-hover:text-accent-secondary
          transition-colors
          duration-300
        ">
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-4 w-4" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M19 9l-7 7-7-7" 
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
