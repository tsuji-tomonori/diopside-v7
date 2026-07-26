import { SVGProps } from 'react';

export type IconName = 'search' | 'sell' | 'calendar_month' | 'tune' | 'home' | 'star' | 'star_filled' | 'history' | 'shuffle' | 'chat_bubble' | 'play_circle' | 'close' | 'chevron_right' | 'chevron_left' | 'account_circle';
const paths: Record<IconName,
  string> = {
  search: 'm21 21-4.35-4.35M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16Z',
  sell: 'M20 12 12 20 4 12V4h8l8 8ZM7 7h.01',
  calendar_month: 'M7 2v4m10-4v4M3 10h18M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z',
  tune: 'M4 7h10m4 0h2M4 17h4m4 0h8M14 4v6M8 14v6',
  home: 'm3 11 9-8 9 8v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1v-9Z',
  star: 'm12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2-4.5-4.4 6.2-.9L12 3Z',
  star_filled: 'm12 2.5 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3.1-5.8 3.1 1.1-6.5-4.7-4.6 6.5-.9L12 2.5Z',
  history: 'M3 12a9 9 0 1 0 3-6.7M3 4v5h5m4-4v7l4 2',
  shuffle: 'M16 3h5v5m0-5-6 6M3 7h3l11 11h4m0-5v5h-5M3 17h3l3-3',
  chat_bubble: 'M4 4h16v12H8l-4 4V4Z',
  play_circle: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-2 5 6 4-6 4V8Z',
  close: 'm6 6 12 12M18 6 6 18',
  chevron_right: 'm9 5 7 7-7 7',
  chevron_left: 'm15 5-7 7 7 7',
  account_circle: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm0 2c-4.4 0-8 2.1-8 4.7V21h16v-2.3c0-2.6-3.6-4.7-8-4.7Z',
};
export function Icon({ name,
  size = 20,
  title,
  ...props }: { name: IconName;
size?: 16 | 20 | 24;
title?: string } & SVGProps<SVGSVGElement>) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill={name === 'star_filled' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden={title ? undefined : true} role={title ? 'img' : undefined} {...props}>{title ? <title>{title}</title> : null}<path d={paths[name]} /></svg>;
}
