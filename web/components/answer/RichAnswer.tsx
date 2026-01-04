import React from 'react';
import { cn } from '@/lib/utils';
import { EvidenceBadge, type EvidenceLevel } from './EvidenceBadge';
import { Callout, type CalloutType } from './Callout';
import { DrugTable } from './DrugTable';
import { DecisionTree } from './DecisionTree';
import { Section } from './Section';
import { DrugCard } from './DrugCard';
import { CopyToEMR, CopyOptions } from './QuickCopy';
import { Clock } from 'lucide-react';

// Types
interface Citation {
  id: string;
  title: string;
  authors?: string[];
  journal?: string;
  year?: number;
  doi?: string;
  pmid?: string;
  url?: string;
}

interface EvidenceBadgeData {
  level: EvidenceLevel;
  strength?: string;
  sourceCount?: number;
  confidenceScore?: number;
  lastUpdated?: string;
}

interface CalloutData {
  type: CalloutType;
  title: string;
  content: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  citations?: Citation[];
}

interface TableData {
  id: string;
  title?: string;
  caption?: string;
  headers: string[];
  rows: Array<{
    cells: Array<{
      value: string;
      alignment?: 'left' | 'center' | 'right';
      emphasis?: boolean;
      color?: string;
    }>;
  }>;
  footer?: string;
}

interface DecisionTreeData {
  id: string;
  title: string;
  description?: string;
  startNode: string;
  nodes: Record<string, any>;
  mermaidDiagram?: string;
}

interface DrugCardData {
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
  evidence?: EvidenceBadgeData;
}

interface SectionData {
  id: string;
  title: string;
  content: string;
  collapsed?: boolean;
  level?: number;
  subsections?: SectionData[];
  evidenceLevel?: EvidenceLevel;
}

interface RichAnswerData {
  query: string;
  summary: string;
  sections: SectionData[];
  tables?: TableData[];
  decisionTrees?: DecisionTreeData[];
  callouts?: CalloutData[];
  drugCards?: DrugCardData[];
  citations: Citation[];
  overallEvidence?: EvidenceBadgeData;
  generatedAt?: string;
}

interface RichAnswerProps {
  data: RichAnswerData;
  className?: string;
  onCopyToEMR?: (content: string) => void;
  onPrescribe?: (drugName: string) => void;
}

export const RichAnswer: React.FC<RichAnswerProps> = ({
  data,
  className,
  onCopyToEMR,
  onPrescribe,
}) => {
  const {
    query,
    summary,
    sections,
    tables = [],
    decisionTrees = [],
    callouts = [],
    drugCards = [],
    citations,
    overallEvidence,
    generatedAt,
  } = data;

  // Generate EMR-formatted text
  const generateEMRText = () => {
    let text = `Query: ${query}\n\n`;
    text += `${summary}\n\n`;

    sections.forEach((section) => {
      if (!section.collapsed) {
        text += `${section.title.toUpperCase()}\n`;
        text += `${section.content}\n\n`;
      }
    });

    if (citations.length > 0) {
      text += 'REFERENCES\n';
      citations.forEach((citation, i) => {
        text += `${i + 1}. ${citation.title}`;
        if (citation.journal && citation.year) {
          text += `. ${citation.journal} (${citation.year})`;
        }
        text += '\n';
      });
    }

    return text;
  };

  const handleCopyToEMR = () => {
    const emrText = generateEMRText();
    onCopyToEMR?.(emrText);
  };

  return (
    <div className={cn('max-w-5xl mx-auto space-y-6', className)}>
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">{query}</h1>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {overallEvidence && (
              <EvidenceBadge
                level={overallEvidence.level}
                strength={overallEvidence.strength as any}
                sourceCount={overallEvidence.sourceCount}
                confidenceScore={overallEvidence.confidenceScore}
                lastUpdated={overallEvidence.lastUpdated}
              />
            )}
            {generatedAt && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                <span>{new Date(generatedAt).toLocaleString()}</span>
              </div>
            )}
          </div>

          <CopyToEMR content={generateEMRText()} />
        </div>
      </div>

      {/* Summary */}
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-2">Summary</h2>
        <p className="text-blue-900">{summary}</p>
      </div>

      {/* Callouts */}
      {callouts.length > 0 && (
        <div className="space-y-3">
          {callouts.map((callout, index) => (
            <Callout
              key={index}
              type={callout.type}
              title={callout.title}
              content={callout.content}
              severity={callout.severity}
              citations={callout.citations}
            />
          ))}
        </div>
      )}

      {/* Drug Cards */}
      {drugCards.length > 0 && (
        <div className="space-y-4">
          {drugCards.map((drug, index) => (
            <DrugCard
              key={index}
              name={drug.name}
              genericName={drug.genericName}
              mechanism={drug.mechanism}
              indications={drug.indications}
              dosing={drug.dosing}
              contraindications={drug.contraindications}
              warnings={drug.warnings}
              interactions={drug.interactions}
              sideEffects={drug.sideEffects}
              monitoring={drug.monitoring}
              evidenceLevel={drug.evidence?.level}
              onPrescribe={() => onPrescribe?.(drug.name)}
            />
          ))}
        </div>
      )}

      {/* Sections */}
      {sections.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          {sections.map((section) => (
            <Section
              key={section.id}
              id={section.id}
              title={section.title}
              content={section.content}
              collapsed={section.collapsed}
              level={section.level}
              subsections={section.subsections}
              evidenceLevel={section.evidenceLevel}
            />
          ))}
        </div>
      )}

      {/* Tables */}
      {tables.length > 0 && (
        <div className="space-y-4">
          {tables.map((table) => (
            <DrugTable
              key={table.id}
              id={table.id}
              title={table.title}
              caption={table.caption}
              headers={table.headers}
              rows={table.rows}
              footer={table.footer}
            />
          ))}
        </div>
      )}

      {/* Decision Trees */}
      {decisionTrees.length > 0 && (
        <div className="space-y-4">
          {decisionTrees.map((tree) => (
            <DecisionTree
              key={tree.id}
              id={tree.id}
              title={tree.title}
              description={tree.description}
              startNode={tree.startNode}
              nodes={tree.nodes}
              mermaidDiagram={tree.mermaidDiagram}
            />
          ))}
        </div>
      )}

      {/* References */}
      {citations.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">References</h2>
          <ol className="space-y-3">
            {citations.map((citation, index) => (
              <li key={citation.id} className="text-sm text-gray-700">
                <span className="font-semibold text-gray-900">[{index + 1}]</span>{' '}
                {citation.authors && citation.authors.length > 0 && (
                  <span>{citation.authors.join(', ')}. </span>
                )}
                <span className="font-medium">{citation.title}</span>
                {citation.journal && <span>. {citation.journal}</span>}
                {citation.year && <span> ({citation.year})</span>}
                {citation.doi && (
                  <span className="ml-2">
                    <a
                      href={`https://doi.org/${citation.doi}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      DOI: {citation.doi}
                    </a>
                  </span>
                )}
                {citation.pmid && (
                  <span className="ml-2">
                    <a
                      href={`https://pubmed.ncbi.nlm.nih.gov/${citation.pmid}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      PMID: {citation.pmid}
                    </a>
                  </span>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
};

export default RichAnswer;
