import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Copy, Check, FileText, Clipboard } from 'lucide-react';

interface QuickCopyProps {
  text: string;
  label?: string;
  variant?: 'default' | 'compact' | 'icon';
  format?: 'plain' | 'markdown' | 'emr';
  className?: string;
  onCopy?: () => void;
}

export const QuickCopy: React.FC<QuickCopyProps> = ({
  text,
  label = 'Copy',
  variant = 'default',
  format = 'plain',
  className,
  onCopy,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      onCopy?.();

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleCopy}
        className={cn(
          'p-2 rounded-md transition-colors',
          copied
            ? 'bg-green-100 text-green-700'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
          className
        )}
        title={label}
      >
        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
      </button>
    );
  }

  if (variant === 'compact') {
    return (
      <button
        onClick={handleCopy}
        className={cn(
          'inline-flex items-center gap-1.5 px-2 py-1 text-xs rounded-md transition-colors',
          copied
            ? 'bg-green-100 text-green-700'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
          className
        )}
      >
        {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
        <span>{copied ? 'Copied!' : label}</span>
      </button>
    );
  }

  return (
    <button
      onClick={handleCopy}
      className={cn(
        'inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
        copied
          ? 'bg-green-600 text-white'
          : 'bg-blue-600 text-white hover:bg-blue-700',
        className
      )}
    >
      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
      <span>{copied ? 'Copied!' : label}</span>
    </button>
  );
};

interface CopyOptionsProps {
  plainText: string;
  formattedText?: string;
  emrText?: string;
  className?: string;
}

export const CopyOptions: React.FC<CopyOptionsProps> = ({
  plainText,
  formattedText,
  emrText,
  className,
}) => {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      <QuickCopy text={plainText} label="Copy Plain Text" variant="compact" />
      {formattedText && (
        <QuickCopy text={formattedText} label="Copy Formatted" variant="compact" />
      )}
      {emrText && (
        <QuickCopy text={emrText} label="Copy for EMR" variant="compact" />
      )}
    </div>
  );
};

interface CopyToEMRProps {
  content: string;
  includeCitations?: boolean;
  className?: string;
}

export const CopyToEMR: React.FC<CopyToEMRProps> = ({
  content,
  includeCitations = false,
  className,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={cn(
        'inline-flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all',
        copied
          ? 'bg-green-600 text-white shadow-lg'
          : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md',
        className
      )}
    >
      {copied ? <Check className="w-5 h-5" /> : <Clipboard className="w-5 h-5" />}
      <span className="font-semibold">{copied ? 'Copied to Clipboard!' : 'Copy to EMR'}</span>
    </button>
  );
};
