import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { CalendarIcon, ExternalLinkIcon } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface UpdateCardProps {
  id: string;
  title: string;
  timestamp: string;
  commitUrl: string;
  gptSummary?: string;
}

export default function UpdateCard({ 
  id, 
  title, 
  timestamp, 
  commitUrl,
  gptSummary
}: UpdateCardProps) {
  const [maxHeight, setMaxHeight] = useState('5rem'); // 初始高度对应5行
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    if (isHovering) {
      const normalizedSummary = gptSummary ? gptSummary.replace(/\\n/g, '\n') : '';
      const totalLines = normalizedSummary.split('\n').length;
      
      // 计算总高度，假设每行约1.5rem
      const totalHeight = `${totalLines * 1.5}rem`;
      
      // 使用CSS过渡实现平滑展开
      setMaxHeight(totalHeight);
    }
  }, [isHovering, gptSummary]);

  const hasMoreLines = gptSummary ? gptSummary.split(/\\n|\n/).length > 5 : false;

  return (
    <div 
      className="cyberpunk-card hover:animate-pulse-glow"
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => {
        setIsHovering(false);
      }}
    >
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-xl text-yellow-400 truncate">{title}</h2>
        <a 
          href={commitUrl} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="text-accent-secondary hover:text-accent-primary transition-colors"
        >
          🔗 Commit
        </a>
      </div>
      <div className="text-text-secondary text-sm mb-2">
        {new Date(timestamp).toLocaleString()}
      </div>
      {gptSummary && (
        <div 
          className="overflow-hidden transition-all duration-500 ease-in-out"
          style={{ 
            maxHeight: maxHeight,
          }}
        >
          <ReactMarkdown 
            className="text-white opacity-80 prose prose-invert"
            remarkPlugins={[remarkGfm]} 
            rehypePlugins={[rehypeRaw]}
            components={{
              a: ({node, ...props}) => (
                <a 
                  {...props} 
                  className="text-accent-secondary hover:text-accent-primary" 
                  target="_blank" 
                  rel="noopener noreferrer"
                />
              )
            }}
          >
            {gptSummary}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}
