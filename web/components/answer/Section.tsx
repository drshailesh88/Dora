import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { CompactEvidenceBadge, type EvidenceLevel } from './EvidenceBadge';
import ReactMarkdown from 'react-markdown';

interface QuickAction {
  label: string;
  actionType: 'copy' | 'calculate' | 'prescribe' | 'order' | 'navigate';
  data?: Record<string, any>;
  icon?: string;
  primary?: boolean;
}

interface SectionProps {
  id: string;
  title: string;
  content: string;
  collapsed?: boolean;
  level?: number;
  subsections?: SectionProps[];
  quickActions?: QuickAction[];
  evidenceLevel?: EvidenceLevel;
  className?: string;
  onActionClick?: (action: QuickAction) => void;
}

export const Section: React.FC<SectionProps> = ({
  id,
  title,
  content,
  collapsed: initialCollapsed = false,
  level = 2,
  subsections = [],
  quickActions = [],
  evidenceLevel,
  className,
  onActionClick,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(initialCollapsed);

  const HeadingTag = `h${Math.min(level, 6)}` as keyof JSX.IntrinsicElements;

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={cn('border-l-2 border-gray-200 pl-4 mb-6', className)} id={id}>
      <div className="flex items-start justify-between mb-3">
        <button
          onClick={toggleCollapse}
          className="flex items-center gap-2 text-left group hover:text-blue-600 transition-colors flex-1"
        >
          <span className="text-gray-400 group-hover:text-blue-500">
            {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </span>
          <HeadingTag className="font-semibold text-gray-900 group-hover:text-blue-600">
            {title}
          </HeadingTag>
          {evidenceLevel && <CompactEvidenceBadge level={evidenceLevel} className="ml-2" />}
        </button>

        {quickActions.length > 0 && !isCollapsed && (
          <div className="flex gap-2 ml-4">
            {quickActions.map((action, index) => (
              <button
                key={index}
                onClick={() => onActionClick?.(action)}
                className={cn(
                  'px-3 py-1 text-xs rounded-md transition-colors',
                  action.primary
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                {action.icon && <span className="mr-1">{action.icon}</span>}
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {!isCollapsed && (
        <div className="space-y-4">
          <div className="prose prose-sm max-w-none text-gray-700">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>

          {subsections.length > 0 && (
            <div className="space-y-4 mt-4">
              {subsections.map((subsection) => (
                <Section
                  key={subsection.id}
                  {...subsection}
                  level={level + 1}
                  onActionClick={onActionClick}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// CollapsibleSections component for managing multiple sections
interface CollapsibleSectionsProps {
  sections: SectionProps[];
  defaultExpanded?: string[];
  className?: string;
  onActionClick?: (action: QuickAction) => void;
}

export const CollapsibleSections: React.FC<CollapsibleSectionsProps> = ({
  sections,
  defaultExpanded = ['overview'],
  className,
  onActionClick,
}) => {
  return (
    <div className={cn('space-y-6', className)}>
      {sections.map((section) => (
        <Section
          key={section.id}
          {...section}
          collapsed={!defaultExpanded.includes(section.id)}
          onActionClick={onActionClick}
        />
      ))}
    </div>
  );
};
