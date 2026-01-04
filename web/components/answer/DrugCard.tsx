import React from 'react';
import { cn } from '@/lib/utils';
import { Pill, AlertTriangle, Info } from 'lucide-react';
import { EvidenceBadge, type EvidenceLevel } from './EvidenceBadge';

interface DrugCardProps {
  name: string;
  genericName?: string;
  className?: string;
  mechanism?: string;
  indications?: string[];
  dosing?: string;
  contraindications?: string[];
  warnings?: string[];
  interactions?: string[];
  sideEffects?: string[];
  monitoring?: string;
  evidenceLevel?: EvidenceLevel;
  onPrescribe?: () => void;
}

export const DrugCard: React.FC<DrugCardProps> = ({
  name,
  genericName,
  className,
  mechanism,
  indications = [],
  dosing,
  contraindications = [],
  warnings = [],
  interactions = [],
  sideEffects = [],
  monitoring,
  evidenceLevel,
  onPrescribe,
}) => {
  return (
    <div
      className={cn(
        'bg-white rounded-lg border-2 border-gray-200 shadow-sm hover:shadow-md transition-shadow',
        className
      )}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <Pill className="w-6 h-6 text-blue-600" />
              <div>
                <h3 className="text-xl font-bold text-gray-900">{name}</h3>
                {genericName && <p className="text-sm text-gray-600 italic">{genericName}</p>}
              </div>
            </div>
          </div>
          {evidenceLevel && (
            <EvidenceBadge level={evidenceLevel} className="flex-shrink-0" />
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-4">
        {/* Mechanism */}
        {mechanism && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-1">Mechanism of Action</h4>
            <p className="text-sm text-gray-600">{mechanism}</p>
          </div>
        )}

        {/* Indications */}
        {indications.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Indications</h4>
            <ul className="space-y-1">
              {indications.map((indication, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  <span>{indication}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Dosing */}
        {dosing && (
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
            <h4 className="text-sm font-semibold text-blue-900 mb-1">Dosing</h4>
            <p className="text-sm text-blue-800 font-medium">{dosing}</p>
          </div>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <div className="bg-red-50 rounded-lg p-3 border border-red-200">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-900 mb-2">Warnings</h4>
                <ul className="space-y-1">
                  {warnings.map((warning, index) => (
                    <li key={index} className="text-sm text-red-800">
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Contraindications */}
        {contraindications.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Contraindications</h4>
            <ul className="space-y-1">
              {contraindications.map((ci, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-red-500 mr-2">✕</span>
                  <span>{ci}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Side Effects */}
        {sideEffects.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Common Side Effects</h4>
            <div className="flex flex-wrap gap-2">
              {sideEffects.map((effect, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md"
                >
                  {effect}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Interactions */}
        {interactions.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Interactions</h4>
            <ul className="space-y-1">
              {interactions.map((interaction, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-orange-500 mr-2">⚡</span>
                  <span>{interaction}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Monitoring */}
        {monitoring && (
          <div className="bg-amber-50 rounded-lg p-3 border border-amber-100">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-amber-900 mb-1">Monitoring</h4>
                <p className="text-sm text-amber-800">{monitoring}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      {onPrescribe && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <button
            onClick={onPrescribe}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Prescribe {name}
          </button>
        </div>
      )}
    </div>
  );
};

// Compact version for lists
interface CompactDrugCardProps {
  name: string;
  genericName?: string;
  dosing?: string;
  className?: string;
  onClick?: () => void;
}

export const CompactDrugCard: React.FC<CompactDrugCardProps> = ({
  name,
  genericName,
  dosing,
  className,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={cn(
        'flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg',
        onClick && 'cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <Pill className="w-5 h-5 text-blue-600" />
        <div>
          <div className="font-medium text-gray-900">{name}</div>
          {genericName && <div className="text-xs text-gray-500 italic">{genericName}</div>}
        </div>
      </div>
      {dosing && <div className="text-sm text-gray-600">{dosing}</div>}
    </div>
  );
};
