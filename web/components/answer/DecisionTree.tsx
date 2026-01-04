import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { GitBranch, Circle, Square, CheckCircle } from 'lucide-react';
import mermaid from 'mermaid';

interface DecisionNode {
  id: string;
  type: 'decision' | 'action' | 'outcome';
  text: string;
  yesNext?: string;
  noNext?: string;
  children?: string[];
  action?: string;
}

interface DecisionTreeProps {
  id: string;
  title: string;
  description?: string;
  startNode: string;
  nodes: Record<string, DecisionNode>;
  mermaidDiagram?: string;
  className?: string;
}

export const DecisionTree: React.FC<DecisionTreeProps> = ({
  id,
  title,
  description,
  startNode,
  nodes,
  mermaidDiagram,
  className,
}) => {
  const [currentNode, setCurrentNode] = useState(startNode);
  const [showDiagram, setShowDiagram] = useState(false);
  const [path, setPath] = useState<string[]>([startNode]);

  const diagramRef = React.useRef<HTMLDivElement>(null);

  // Render Mermaid diagram
  React.useEffect(() => {
    if (showDiagram && mermaidDiagram && diagramRef.current) {
      mermaid.initialize({ startOnLoad: false, theme: 'default' });
      mermaid.render(`mermaid-${id}`, mermaidDiagram).then(({ svg }) => {
        if (diagramRef.current) {
          diagramRef.current.innerHTML = svg;
        }
      });
    }
  }, [showDiagram, mermaidDiagram, id]);

  const handleDecision = (nextNodeId: string, answer: 'yes' | 'no') => {
    setCurrentNode(nextNodeId);
    setPath([...path, nextNodeId]);
  };

  const handleReset = () => {
    setCurrentNode(startNode);
    setPath([startNode]);
  };

  const current = nodes[currentNode];

  if (!current) {
    return (
      <div className="text-red-600">
        Error: Node not found
      </div>
    );
  }

  const renderNode = (node: DecisionNode) => {
    switch (node.type) {
      case 'decision':
        return (
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
              <GitBranch className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h4 className="font-semibold text-blue-900 mb-2">{node.text}</h4>
                <div className="flex gap-3">
                  {node.yesNext && (
                    <button
                      onClick={() => handleDecision(node.yesNext!, 'yes')}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
                    >
                      Yes
                    </button>
                  )}
                  {node.noNext && (
                    <button
                      onClick={() => handleDecision(node.noNext!, 'no')}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
                    >
                      No
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case 'action':
        return (
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-amber-50 border-2 border-amber-200 rounded-lg">
              <Square className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h4 className="font-semibold text-amber-900 mb-2">Action</h4>
                <p className="text-amber-800">{node.text}</p>
                {node.children && node.children.length > 0 && (
                  <button
                    onClick={() => setCurrentNode(node.children![0])}
                    className="mt-3 px-4 py-2 bg-amber-600 text-white rounded-lg font-medium hover:bg-amber-700 transition-colors"
                  >
                    Continue
                  </button>
                )}
              </div>
            </div>
          </div>
        );

      case 'outcome':
        return (
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h4 className="font-semibold text-green-900 mb-2">Outcome</h4>
                <p className="text-green-800">{node.text}</p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 shadow-sm', className)}>
      {/* Header */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900">{title}</h3>
            {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowDiagram(!showDiagram)}
              className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              {showDiagram ? 'Hide' : 'Show'} Diagram
            </button>
            <button
              onClick={handleReset}
              className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Diagram view */}
      {showDiagram && mermaidDiagram && (
        <div className="p-6 bg-gray-50 border-b border-gray-200 overflow-x-auto">
          <div ref={diagramRef} className="flex justify-center" />
        </div>
      )}

      {/* Interactive view */}
      <div className="p-6">
        {/* Breadcrumb */}
        <div className="mb-6 flex items-center gap-2 text-sm text-gray-600">
          <span className="font-medium">Path:</span>
          {path.map((nodeId, index) => (
            <React.Fragment key={nodeId}>
              {index > 0 && <span className="text-gray-400">→</span>}
              <button
                onClick={() => {
                  setCurrentNode(nodeId);
                  setPath(path.slice(0, index + 1));
                }}
                className="hover:text-blue-600 hover:underline"
              >
                Step {index + 1}
              </button>
            </React.Fragment>
          ))}
        </div>

        {/* Current node */}
        {renderNode(current)}
      </div>
    </div>
  );
};

// Simplified static view
interface StaticDecisionTreeProps {
  title: string;
  mermaidDiagram: string;
  className?: string;
}

export const StaticDecisionTree: React.FC<StaticDecisionTreeProps> = ({
  title,
  mermaidDiagram,
  className,
}) => {
  const diagramRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (mermaidDiagram && diagramRef.current) {
      mermaid.initialize({ startOnLoad: false, theme: 'default' });
      mermaid.render(`static-mermaid-${title}`, mermaidDiagram).then(({ svg }) => {
        if (diagramRef.current) {
          diagramRef.current.innerHTML = svg;
        }
      });
    }
  }, [mermaidDiagram, title]);

  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 p-6', className)}>
      <h3 className="text-lg font-bold text-gray-900 mb-4">{title}</h3>
      <div ref={diagramRef} className="overflow-x-auto" />
    </div>
  );
};
