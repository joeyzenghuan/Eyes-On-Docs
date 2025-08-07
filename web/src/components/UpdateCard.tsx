import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { CalendarIcon, ExternalLinkIcon, Copy } from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { toast } from 'sonner';

interface UpdateCardProps {
  id: string;
  title: string;
  tag?: string;
  timestamp: string;
  commitUrl: string;
  gptSummary?: string;
}

export default function UpdateCard({ 
  id, 
  title, 
  tag,
  timestamp, 
  commitUrl,
  gptSummary
}: UpdateCardProps) {
  const [maxHeight, setMaxHeight] = useState('5rem'); // 初始高度对应5行
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
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
    ? (typeof gptSummary === 'string' 
        ? gptSummary.split(/\n|\n/).length > 5 
        : false)
    : false;

  // 复制卡片内容的函数
  const copyCardContent = () => {
    const content = `标题: ${title}
标签: ${tag}
时间: ${timestamp}
内容: ${typeof gptSummary === 'string' ? gptSummary : JSON.stringify(gptSummary)}
链接: ${commitUrl}`;

    navigator.clipboard.writeText(content).then(() => {
      toast.success('内容已复制到剪贴板');
    }).catch(err => {
      toast.error('复制失败');
      console.error('复制失败:', err);
    });
  };

  return (
    <div 
      className="cyberpunk-card hover:animate-pulse-glow w-full max-w-full relative"
      onMouseEnter={handleMouseEnter}
      onClick={toggleExpand}
    >
      <div className="flex justify-between items-center mb-2 w-full">
        <div className="flex items-center space-x-2 w-full">
          {tag && (
            <span className="bg-accent-secondary text-black px-2 py-0.5 rounded-md text-xs font-semibold">
              {tag}
            </span>
          )}
          <h2 className="text-xl text-yellow-400 break-words flex-grow">{title}</h2>
        </div>
        <div className="flex items-center space-x-2">
          <button 
            onClick={(e) => {
              e.stopPropagation();
              copyCardContent();
            }}
            className={`
              p-1.5 rounded-md transition-all duration-300 flex items-center justify-center
              ${isCopied 
                ? 'bg-green-500 text-white' 
                : 'bg-background-secondary text-text-secondary hover:bg-accent-secondary'}
            `}
            title="Copy card content"
          >
            <Copy size={16} />
          </button>
          <a 
            href={commitUrl} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="
              p-1.5 rounded-md transition-all duration-300 flex items-center justify-center
              bg-background-secondary text-text-secondary hover:bg-accent-secondary
            "
            onClick={(e) => {
              e.stopPropagation(); // Prevent card expand when clicking commit link
            }}
            title="View commit"
          >
            <ExternalLinkIcon size={16} />
          </a>
        </div>
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
