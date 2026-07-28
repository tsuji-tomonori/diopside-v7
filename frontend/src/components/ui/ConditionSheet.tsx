import { KeyboardEvent, ReactNode, useLayoutEffect, useRef } from 'react';

import { Icon } from './Icon';

type ConditionSheetProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  resultCount?: number;
  initialSection?: string;
};

const focusableSelector = [
  'button:not(:disabled)',
  'input:not(:disabled)',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

export function ConditionSheet({
  open,
  onClose,
  title = '検索条件',
  children,
  resultCount,
  initialSection,
}: ConditionSheetProps) {
  const sheetRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);

  useLayoutEffect(() => {
    if (open) {
      triggerRef.current = document.activeElement as HTMLElement;
      wasOpenRef.current = true;
      sheetRef.current?.focus({ preventScroll: true });
      if (!initialSection) {
        return;
      }
      const section = sheetRef.current?.querySelector<HTMLElement>(`#${initialSection}`);
      const body = sheetRef.current?.querySelector<HTMLElement>('.dio-condition-sheet__body');
      if (section && body) {
        const top = Math.max(0, section.offsetTop - body.offsetTop - 8);
        if (top > 0) {
          body.scrollTo({ top });
        }
      }
      section?.classList.add('is-highlighted');
      window.setTimeout(() => section?.classList.remove('is-highlighted'), 1200);
      return;
    }

    if (wasOpenRef.current) {
      triggerRef.current?.focus();
      wasOpenRef.current = false;
    }
  }, [initialSection, open]);

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape') {
      onClose();
      return;
    }

    if (event.key !== 'Tab') {
      return;
    }

    const focusable = Array.from(
      sheetRef.current?.querySelectorAll<HTMLElement>(focusableSelector) ?? [],
    );
    const first = focusable.at(0);
    const last = focusable.at(-1);

    if (!first || !last) {
      event.preventDefault();
      return;
    }

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  if (!open) {
    return null;
  }

  return (
    <div
      className="dio-sheet-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        aria-labelledby="condition-sheet-title"
        aria-modal="true"
        className="dio-condition-sheet"
        onKeyDown={handleKeyDown}
        ref={sheetRef}
        role="dialog"
        tabIndex={-1}
      >
        <div className="dio-sheet-handle" />
        <header>
          <h2 id="condition-sheet-title">{title}</h2>
          <button aria-label="条件を閉じる" onClick={onClose} type="button">
            <Icon name="close" size={20} />
          </button>
        </header>
        <div className="dio-condition-sheet__body" data-initial-section={initialSection}>
          {children}
        </div>
        <button
          className="dio-button dio-button--primary dio-condition-sheet__cta"
          onClick={onClose}
          type="button"
        >
          {resultCount === 0 ? '0件 — 条件をゆるめる' : `${resultCount ?? 0}件を表示`}
        </button>
      </div>
    </div>
  );
}
