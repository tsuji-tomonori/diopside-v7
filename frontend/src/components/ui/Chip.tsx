import { ButtonHTMLAttributes } from 'react';

import { Icon } from './Icon';

type ChipProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'selectable' | 'removable' | 'add' | 'action' | 'preset';
  selected?: boolean;
  label: string;
  count?: number;
  onRemove?: () => void;
};

export function Chip({
  variant = 'selectable',
  selected = false,
  label,
  count,
  onRemove,
  className = '',
  ...props
}: ChipProps) {
  if (variant === 'removable') {
    return (
      <span className={`dio-chip dio-chip--removable ${className}`}>
        <button className="dio-chip__label" type="button" {...props}>
          {label}
        </button>
        <button
          aria-label={`${label}の条件を解除`}
          className="dio-chip__remove"
          onClick={onRemove}
          type="button"
        >
          <Icon name="close" size={16} />
        </button>
      </span>
    );
  }

  return (
    <button
      aria-pressed={variant === 'selectable' || variant === 'preset' ? selected : undefined}
      className={`dio-chip dio-chip--${variant} ${selected ? 'is-selected' : ''} ${className}`}
      {...props}
    >
      {variant === 'action' ? <Icon name="tune" size={16} /> : null}
      {variant === 'add' ? '＋' : null}
      {label}
      {typeof count === 'number' ? <span className="dio-num">({count})</span> : null}
    </button>
  );
}
