'use client';

import { useState, useEffect } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface TypewriterMessageProps {
  content: string;
  isNew?: boolean;
  className?: string;
}

export default function TypewriterMessage({ content, isNew = false, className = '' }: TypewriterMessageProps) {
  const [displayedContent, setDisplayedContent] = useState('');
  const [isTyping, setIsTyping] = useState(isNew);

  useEffect(() => {
    if (!isNew) {
      setDisplayedContent(content);
      return;
    }

    setIsTyping(true);
    let index = 0;
    const typingSpeed = 20; // milliseconds per character

    const timer = setInterval(() => {
      if (index < content.length) {
        setDisplayedContent(content.slice(0, index + 1));
        index++;
      } else {
        setIsTyping(false);
        clearInterval(timer);
      }
    }, typingSpeed);

    return () => clearInterval(timer);
  }, [content, isNew]);

  // Configure marked options
  marked.setOptions({
    breaks: true,
    gfm: true,
  });

  // Parse and sanitize markdown
  const htmlContent = DOMPurify.sanitize(marked.parse(displayedContent) as string, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'code', 'pre', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'a'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
  });

  return (
    <div className={className}>
      <div
        className="markdown-content prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
      {isTyping && (
        <span className="inline-block w-1 h-4 bg-current ml-0.5 animate-pulse"></span>
      )}
      <style dangerouslySetInnerHTML={{
        __html: `
          .markdown-content {
            line-height: 1.6;
          }
          .markdown-content p {
            margin: 0.5rem 0;
          }
          .markdown-content ol {
            list-style-type: decimal;
            list-style-position: outside;
            padding-left: 1.75rem;
            margin: 0.75rem 0;
          }
          .markdown-content ul {
            list-style-type: disc;
            list-style-position: outside;
            padding-left: 1.75rem;
            margin: 0.75rem 0;
          }
          .markdown-content li {
            margin: 0.35rem 0;
            display: list-item;
          }
          .markdown-content strong {
            font-weight: 700;
            color: #1f2937;
          }
          .markdown-content em {
            font-style: italic;
          }
          .markdown-content code {
            background-color: #f3f4f6;
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
            font-size: 0.9em;
            font-family: monospace;
          }
          .markdown-content pre {
            background-color: #f3f4f6;
            padding: 0.75rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            margin: 0.75rem 0;
          }
          .markdown-content pre code {
            background: none;
            padding: 0;
          }
          .markdown-content a {
            color: #2563eb;
            text-decoration: none;
          }
          .markdown-content a:hover {
            text-decoration: underline;
          }
          .markdown-content h1, .markdown-content h2, .markdown-content h3,
          .markdown-content h4, .markdown-content h5, .markdown-content h6 {
            font-weight: 700;
            margin: 1rem 0 0.5rem 0;
            color: #111827;
          }
          .markdown-content h1 { font-size: 1.5rem; }
          .markdown-content h2 { font-size: 1.3rem; }
          .markdown-content h3 { font-size: 1.1rem; }
          .markdown-content blockquote {
            border-left: 4px solid #e5e7eb;
            padding-left: 1rem;
            margin: 0.75rem 0;
            color: #6b7280;
          }
        `
      }} />
    </div>
  );
}
