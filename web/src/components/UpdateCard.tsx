import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { CalendarIcon, ExternalLinkIcon } from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';
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
  const [isExpanded, setIsExpanded] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) {
      // 处理可能的转义换行符
      const normalizedSummary = gptSummary 
        ? gptSummary
            .replace(/\\n/g, '\n')  // 替换转义的换行符
            .replace(/\\t/g, '    ')  // 替换转义的制表符
            .replace(/\\r/g, '')      // 移除回车符
      : '';

      // 在下一个渲染周期测量实际高度
      requestAnimationFrame(() => {
        const contentHeight = contentRef.current 
          ? contentRef.current.scrollHeight 
          : 0;
        
        // 设置完整高度
        setMaxHeight(`${contentHeight + 20}px`);
      });
    }
  }, [gptSummary]);

  const handleMouseEnter = () => {
    // 如果当前未展开，则展开
    if (!isExpanded) {
      setIsExpanded(true);
    }
  };

  const toggleExpand = () => {
    setIsExpanded(prev => !prev);
  };

  const hasMoreLines = gptSummary 
    ? gptSummary.split(/\\n|\n/).length > 5 
    : false;

  return (
    <div 
      className="cyberpunk-card hover:animate-pulse-glow w-full max-w-full"
      onMouseEnter={handleMouseEnter}
      onClick={toggleExpand}
    >
      <div className="flex justify-between items-center mb-2 w-full">
        <h2 className="text-xl text-yellow-400 w-full break-words flex-grow">{title}</h2>
        <a 
          href={commitUrl} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="text-accent-secondary hover:text-accent-primary transition-colors ml-2"
          onClick={(e) => {
            e.stopPropagation(); // Prevent card expand when clicking commit link
          }}
        >
          🔗 Commit
        </a>
      </div>
      <div className="text-text-secondary text-sm mb-2 w-full">
        {new Date(timestamp).toLocaleString()}
      </div>
      {gptSummary && (
        <div 
          className="overflow-hidden transition-all duration-500 ease-in-out w-full max-w-full cursor-pointer"
          style={{ 
            maxHeight: isExpanded ? maxHeight : '5rem',
          }}
        >
          <div ref={contentRef}>
            <ReactMarkdown 
              className="prose prose-invert text-white opacity-80
                prose-ul:list-disc 
                prose-ul:pl-5 
                prose-li:text-white 
                prose-li:marker:text-yellow-400
                prose-code:bg-black 
                prose-code:text-yellow-400 
                prose-code:px-1 
                prose-code:py-0.5 
                prose-code:rounded 
                prose-code:font-normal
                w-full max-w-full"
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
              {gptSummary.replace(/\\n/g, '\n')}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
