import { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'text';
};

export function Button({
  variant = 'secondary',
  children,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button className={`dio-button dio-button--${variant} ${className}`} {...props}>
      {children}
    </button>
  );
}
