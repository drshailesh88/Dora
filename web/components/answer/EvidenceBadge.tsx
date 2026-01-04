import React from 'react';
import { cn } from '@/lib/utils';

export type EvidenceLevel = 'A' | 'B' | 'C' | 'D' | 'E' | 'Unknown';
export type RecommendationStrength = 'Strong' | 'Weak' | 'Conditional' | 'Insufficient';

interface EvidenceBadgeProps {
  level: EvidenceLevel;
  strength?: RecommendationStrength;
  sourceCount?: number;
  confidenceScore?: number;
  lastUpdated?: string;
  className?: string;
  showTooltip?: boolean;
}

const evidenceColors: Record<EvidenceLevel, { bg: string; text: string; icon: string }> = {
  A: { bg: 'bg-green-100', text: 'text-green-800', icon: '🟢' },
  B: { bg: 'bg-blue-100', text: 'text-blue-800', icon: '🔵' },
  C: { bg: 'bg-amber-100', text: 'text-amber-800', icon: '🟡' },
  D: { bg: 'bg-red-100', text: 'text-red-800', icon: '🔴' },
  E: { bg: 'bg-gray-100', text: 'text-gray-800', icon: '⚫' },
  Unknown: { bg: 'bg-gray-100', text: 'text-gray-800', icon: '⚪' },
};

const evidenceDescriptions: Record<EvidenceLevel, string> = {
  A: 'Multiple RCTs or meta-analyses',
  B: 'Single RCT or large observational study',
  C: 'Expert consensus or small studies',
  D: 'Expert opinion only',
  E: 'Insufficient evidence',
  Unknown: 'Evidence level not assessed',
};

export const EvidenceBadge: React.FC<EvidenceBadgeProps> = ({
  level,
  strength,
  sourceCount = 0,
  confidenceScore = 0,
  lastUpdated,
  className,
  showTooltip = true,
}) => {
  const colors = evidenceColors[level];
  const description = evidenceDescriptions[level];

  const tooltipContent = showTooltip ? (
    <div className="absolute z-10 invisible group-hover:visible w-64 p-3 mt-2 text-sm bg-white border border-gray-200 rounded-lg shadow-lg">
      <div className="font-semibold mb-1">Evidence Level {level}</div>
      <div className="text-gray-600 mb-2">{description}</div>
      {strength && (
        <div className="text-sm">
          <span className="font-medium">Strength:</span> {strength}
        </div>
      )}
      {sourceCount > 0 && (
        <div className="text-sm">
          <span className="font-medium">Sources:</span> {sourceCount}
        </div>
      )}
      {confidenceScore > 0 && (
        <div className="text-sm">
          <span className="font-medium">Confidence:</span> {Math.round(confidenceScore * 100)}%
        </div>
      )}
      {lastUpdated && (
        <div className="text-xs text-gray-500 mt-1">
          Updated: {new Date(lastUpdated).toLocaleDateString()}
        </div>
      )}
    </div>
  ) : null;

  return (
    <div className={cn('relative inline-block group', className)}>
      <div
        className={cn(
          'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium',
          colors.bg,
          colors.text
        )}
      >
        <span className="text-base">{colors.icon}</span>
        <span>Level {level}</span>
        {confidenceScore > 0 && (
          <span className="text-xs opacity-75">{Math.round(confidenceScore * 100)}%</span>
        )}
      </div>
      {tooltipContent}
    </div>
  );
};

interface CompactEvidenceBadgeProps {
  level: EvidenceLevel;
  className?: string;
}

export const CompactEvidenceBadge: React.FC<CompactEvidenceBadgeProps> = ({ level, className }) => {
  const colors = evidenceColors[level];

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold',
        colors.bg,
        colors.text,
        className
      )}
      title={`Evidence Level ${level}`}
    >
      {level}
    </span>
  );
};
