import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { CalendarIcon, ExternalLinkIcon } from 'lucide-react';

interface UpdateCardProps {
  title: string;
  summary: string;
  gptSummary?: string;
  timestamp: string;
  documentUrl: string;
  commitUrl: string;
  product: string;
  language: string;
}

export function UpdateCard({
  title,
  summary,
  gptSummary,
  timestamp,
  documentUrl,
  commitUrl,
  product,
  language,
}: UpdateCardProps) {
  // Add console log to check the props
  console.log('UpdateCard Props:', {
    title,
    summary,
    gptSummary,
    timestamp,
    documentUrl,
    commitUrl,
    product,
    language
  });

  const date = new Date(timestamp).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <Card className="w-full hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <CardTitle className="text-xl font-bold">{title}</CardTitle>
          <div className="flex space-x-2">
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-sm">
              {product}
            </span>
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-md text-sm">
              {language}
            </span>
          </div>
        </div>
        <div className="flex items-center text-sm text-gray-500 mt-2">
          <CalendarIcon className="w-4 h-4 mr-1" />
          {date}
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-600 mb-4">{summary}</p>
        {gptSummary && gptSummary.trim() !== '' && (
          <div className="bg-blue-50 p-3 rounded-md mb-4">
            <p className="text-blue-800 text-sm whitespace-pre-wrap">{gptSummary}</p>
          </div>
        )}
        <div className="flex space-x-4">
          <a
            href={documentUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-blue-600 hover:text-blue-800"
          >
            <ExternalLinkIcon className="w-4 h-4 mr-1" />
            View Documentation
          </a>
          <a
            href={commitUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-blue-600 hover:text-blue-800"
          >
            <ExternalLinkIcon className="w-4 h-4 mr-1" />
            View Changes
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
