import { marked } from 'marked';
import DOMPurify from 'dompurify';
import React from 'react';

interface BubbleProps {
  content: string;
  isUser: boolean;
  timestamp?: string;
}

export function Bubble({ content, isUser, timestamp }: BubbleProps) {
  // Configure marked options
  marked.setOptions({
    breaks: true,
    gfm: true,
  });

  // Parse markdown and sanitize HTML
  const getMarkdownContent = () => {
    const rawMarkup = marked(content);
    const cleanMarkup = DOMPurify.sanitize(rawMarkup as string);
    return { __html: cleanMarkup };
  };

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={`max-w-[70%] rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
        }`}
      >
        <div
          className="prose prose-sm max-w-none dark:prose-invert"
          dangerouslySetInnerHTML={getMarkdownContent()}
        />
        {timestamp && (
          <div
            className={`text-xs mt-1 ${
              isUser ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            {new Date(timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
