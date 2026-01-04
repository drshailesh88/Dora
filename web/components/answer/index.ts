/**
 * Rich Answer Components
 *
 * Comprehensive component library for displaying formatted medical answers
 * with evidence badges, tables, decision trees, and more.
 */

export { RichAnswer } from './RichAnswer';
export type { default as RichAnswerData } from './RichAnswer';

export { EvidenceBadge, CompactEvidenceBadge } from './EvidenceBadge';
export type { EvidenceLevel, RecommendationStrength } from './EvidenceBadge';

export { Callout, WarningCallout, CautionCallout, InfoCallout, TipCallout } from './Callout';
export type { CalloutType, SeverityLevel } from './Callout';

export { DrugTable } from './DrugTable';
export { DrugCard, CompactDrugCard } from './DrugCard';
export { DecisionTree, StaticDecisionTree } from './DecisionTree';
export { Section, CollapsibleSections } from './Section';
export { QuickCopy, CopyOptions, CopyToEMR } from './QuickCopy';
