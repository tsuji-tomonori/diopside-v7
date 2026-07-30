import { ReactNode } from 'react';

interface Props {
  name: 'home' | 'search' | 'saved' | 'history' | 'external' | 'play' | 'shuffle';
}

const paths: Record<Props['name'], ReactNode> = {
  home: (
    <>
      <path d="M3.5 10.5 12 3.8l8.5 6.7" />
      <path d="M5.5 9.5v10h13v-10M9.5 19.5v-6h5v6" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m15.5 15.5 5 5" />
    </>
  ),
  saved: <path d="M6.5 3.5h11v17l-5.5-3.8-5.5 3.8z" />,
  history: (
    <>
      <path d="M4.2 8.2A8.5 8.5 0 1 1 3.5 14" />
      <path d="M4.2 3.8v4.4H8.6M12 7.5v5l3.2 2" />
    </>
  ),
  external: (
    <>
      <path d="M13 4h7v7M20 4l-9 9" />
      <path d="M18 13v6H5V6h6" />
    </>
  ),
  play: <path d="m8 5 11 7-11 7z" />,
  shuffle: (
    <>
      <path d="M4 7h2.5c4.5 0 6.5 10 11 10H20" />
      <path d="m17 14 3 3-3 3M4 17h2.5c1.8 0 3.2-1.6 4.5-3.5M14 7.8c1-1 2.1-1.8 3.5-1.8H20" />
      <path d="m17 3 3 3-3 3" />
    </>
  ),
};

export function NavIcon({ name }: Props) {
  return (
    <svg
      aria-hidden="true"
      className="icon"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    >
      {paths[name]}
    </svg>
  );
}
