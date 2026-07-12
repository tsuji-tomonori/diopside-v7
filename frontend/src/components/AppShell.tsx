import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface AppShellProps {
  children: ReactNode;
}

const navItems = [
  { label: 'ホーム', to: '/' },
  { label: '検索', to: '/search' },
  { label: '保存', to: '/saved' },
  { label: '履歴', to: '/history' },
];

export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const active = location.pathname;

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="main navigation">
        <div className="wordmark">diopside</div>
        <nav>
          {navItems.map((item) => (
            <Link
              key={item.to}
              className={active === item.to ? 'is-active' : ''}
              to={item.to}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        {children}
      </main>

      <nav className="bottom-nav" aria-label="mobile navigation">
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={active === item.to ? 'is-active' : ''}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
