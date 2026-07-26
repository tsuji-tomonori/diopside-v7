import { ReactNode } from 'react';

import { ConditionSheet } from './ConditionSheet';

type ConditionPanelProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  resultCount?: number;
  initialSection?: string;
};

export function ConditionPanel(props: ConditionPanelProps) {
  return (
    <aside aria-label="検索条件パネル" className="dio-condition-panel">
      <ConditionSheet {...props} />
    </aside>
  );
}
