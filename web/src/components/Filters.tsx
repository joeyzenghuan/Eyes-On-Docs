"use client";

import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useRouter, useSearchParams } from 'next/navigation';

interface FiltersProps {
  products: string[];
  languages: string[];
}

export default function Filters({ products, languages }: FiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const currentProduct = searchParams.get('product') || '';
  const currentLanguage = searchParams.get('language') || '';

  const handleProductChange = (value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value && value !== 'ALL_PRODUCTS') {
      params.set('product', value);
    } else {
      params.delete('product');
    }
    params.delete('page'); // Reset to first page
    router.push(`?${params.toString()}`);
  };

  const handleLanguageChange = (value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value && value !== 'ALL_LANGUAGES') {
      params.set('language', value);
    } else {
      params.delete('language');
    }
    params.delete('page'); // Reset to first page
    router.push(`?${params.toString()}`);
  };

  return (
    <div className="flex space-x-4 mb-6">
      <div className="w-48">
        <Select 
          value={currentProduct || 'ALL_PRODUCTS'} 
          onValueChange={handleProductChange}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select Product" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL_PRODUCTS">All Products</SelectItem>
            {products.map((product) => (
              <SelectItem key={product} value={product}>
                {product}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="w-48">
        <Select 
          value={currentLanguage || 'ALL_LANGUAGES'} 
          onValueChange={handleLanguageChange}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select Language" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL_LANGUAGES">All Languages</SelectItem>
            {languages.map((language) => (
              <SelectItem key={language} value={language}>
                {language}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
