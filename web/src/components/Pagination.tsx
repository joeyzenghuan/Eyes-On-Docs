import { Button } from './ui/button';
import { ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange?: (page: number) => void;
}

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange
}: PaginationProps) {
  const generatePageNumbers = () => {
    const maxPagesToShow = 5;
    const halfPagesToShow = Math.floor(maxPagesToShow / 2);

    let startPage = Math.max(1, currentPage - halfPagesToShow);
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

    if (endPage - startPage + 1 < maxPagesToShow) {
      startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    const pageNumbers = [];
    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }

    return pageNumbers;
  };

  const pageNumbers = generatePageNumbers();

  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="text-text-secondary text-sm">
        Showing {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, totalItems)} of {totalItems} updates
      </div>
      <nav className="flex space-x-2">
        {pageNumbers.map(number => (
          <button
            key={number}
            onClick={() => onPageChange(number)}
            className={`
              px-3 py-1 rounded-md transition-all duration-300
              ${currentPage === number 
                ? 'bg-accent-primary text-background-primary' 
                : 'bg-background-secondary text-text-secondary hover:bg-accent-secondary'}
            `}
          >
            {number}
          </button>
        ))}
      </nav>
    </div>
  );
}
