import React from 'react';
import { cn } from '@/lib/utils';
import { AlertCircle, AlertTriangle, Info, Lightbulb, FileText, CheckCircle } from 'lucide-react';

export type CalloutType = 'warning' | 'caution' | 'info' | 'tip' | 'evidence' | 'action';
export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

interface CalloutProps {
  type: CalloutType;
  title: string;
  content: string;
  severity?: SeverityLevel;
  icon?: React.ReactNode;
  citations?: Array<{ id: string; title: string }>;
  className?: string;
}

const calloutConfig: Record<
  CalloutType,
  {
    icon: React.ComponentType<{ className?: string }>;
    defaultBg: string;
    borderColor: string;
    iconColor: string;
  }
> = {
  warning: {
    icon: AlertTriangle,
    defaultBg: 'bg-red-50',
    borderColor: 'border-red-200',
    iconColor: 'text-red-600',
  },
  caution: {
    icon: AlertCircle,
    defaultBg: 'bg-orange-50',
    borderColor: 'border-orange-200',
    iconColor: 'text-orange-600',
  },
  info: {
    icon: Info,
    defaultBg: 'bg-blue-50',
    borderColor: 'border-blue-200',
    iconColor: 'text-blue-600',
  },
  tip: {
    icon: Lightbulb,
    defaultBg: 'bg-green-50',
    borderColor: 'border-green-200',
    iconColor: 'text-green-600',
  },
  evidence: {
    icon: FileText,
    defaultBg: 'bg-purple-50',
    borderColor: 'border-purple-200',
    iconColor: 'text-purple-600',
  },
  action: {
    icon: CheckCircle,
    defaultBg: 'bg-emerald-50',
    borderColor: 'border-emerald-200',
    iconColor: 'text-emerald-600',
  },
};

export const Callout: React.FC<CalloutProps> = ({
  type,
  title,
  content,
  severity = 'medium',
  icon,
  citations,
  className,
}) => {
  const config = calloutConfig[type];
  const Icon = config.icon;

  // Override background for critical severity
  const bgColor =
    severity === 'critical' && (type === 'warning' || type === 'caution')
      ? 'bg-red-100'
      : config.defaultBg;

  return (
    <div
      className={cn(
        'rounded-lg border-l-4 p-4',
        bgColor,
        config.borderColor,
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn('flex-shrink-0 mt-0.5', config.iconColor)}>
          {icon || <Icon className="w-5 h-5" />}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className={cn('font-semibold text-sm mb-1', config.iconColor)}>{title}</h4>
          <div className="text-sm text-gray-700 whitespace-pre-wrap">{content}</div>
          {citations && citations.length > 0 && (
            <div className="mt-2 text-xs text-gray-500">
              <div className="font-medium mb-1">References:</div>
              <ul className="list-disc list-inside space-y-0.5">
                {citations.map((citation) => (
                  <li key={citation.id}>{citation.title}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Convenience components
export const WarningCallout: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="warning" {...props} />
);

export const CautionCallout: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="caution" {...props} />
);

export const InfoCallout: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="info" {...props} />
);

export const TipCallout: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="tip" {...props} />
);
