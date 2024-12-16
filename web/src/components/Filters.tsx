"use client";

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface FiltersProps {
  products: string[];
  languages: string[];
}

export default function Filters({ products, languages }: FiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentProduct = searchParams.get('product') || products[0];
  const currentLanguage = searchParams.get('language') || languages[0];

  const handleProductChange = (product: string) => {
    const params = new URLSearchParams(searchParams);
    params.set('product', product);
    router.push(`/?${params.toString()}`);
  };

  const handleLanguageChange = (language: string) => {
    const params = new URLSearchParams(searchParams);
    params.set('language', language);
    router.push(`/?${params.toString()}`);
  };

  return (
    <div className="flex space-x-6 items-center">
      <div className="relative group">
        <label 
          htmlFor="product" 
          className="block text-xl font-bold mb-2 text-text-secondary 
                     transform transition-all duration-300 
                     group-hover:text-accent-primary 
                     group-hover:translate-x-1 
                     tracking-wider uppercase"
        >
          Product
        </label>
        <div className="relative">
          <select
            id="product"
            name="product"
            value={currentProduct}
            onChange={(e) => handleProductChange(e.target.value)}
            className="cyberpunk-input w-full px-4 py-3 text-lg 
                       appearance-none 
                       bg-background-secondary 
                       border-2 border-border-color 
                       focus:border-accent-secondary 
                       transition-all duration-300 
                       cursor-pointer"
          >
            {products.map((product) => (
              <option 
                key={product} 
                value={product} 
                className="bg-background-secondary text-text-primary"
              >
                {product}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-text-secondary">
            <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
              <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
            </svg>
          </div>
        </div>
      </div>

      <div className="relative group">
        <label 
          htmlFor="language" 
          className="block text-xl font-bold mb-2 text-text-secondary 
                     transform transition-all duration-300 
                     group-hover:text-accent-primary 
                     group-hover:translate-x-1 
                     tracking-wider uppercase"
        >
          Language
        </label>
        <div className="relative">
          <select
            id="language"
            name="language"
            value={currentLanguage}
            onChange={(e) => handleLanguageChange(e.target.value)}
            className="cyberpunk-input w-full px-4 py-3 text-lg 
                       appearance-none 
                       bg-background-secondary 
                       border-2 border-border-color 
                       focus:border-accent-secondary 
                       transition-all duration-300 
                       cursor-pointer"
          >
            {languages.map((language) => (
              <option 
                key={language} 
                value={language} 
                className="bg-background-secondary text-text-primary"
              >
                {language}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-text-secondary">
            <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
              <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
