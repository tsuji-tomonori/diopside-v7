import { ReactNode } from 'react';

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <section className="dio-empty-state">
      <h2 className="dio-display">{title}</h2>
      {children}
    </section>
  );
}
