import { ReactNode, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { storageErrorEvent } from '@/lib/storage';
import { Icon, IconName } from '@/components/ui/Icon';

interface AppShellProps {
  children: ReactNode;
}

const navItems = [
  { label: 'ホーム', to: '/', icon: 'home' },
  { label: '検索', to: '/search', icon: 'search' },
  { label: '保存', to: '/saved', icon: 'star' },
  { label: '履歴', to: '/history', icon: 'history' },
] as { label: string; to: string; icon: IconName }[];

export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const active = location.pathname;
  const [storageError, setStorageError] = useState(false);

  useEffect(() => {
    const reportStorageFailure = () => setStorageError(true);
    window.addEventListener(storageErrorEvent, reportStorageFailure);
    return () => window.removeEventListener(storageErrorEvent, reportStorageFailure);
  }, []);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">本文へスキップ</a>
      <aside className="sidebar">
        <div className="wordmark">diopside</div>
        <nav aria-label="main navigation">
          {navItems.map((item) => (
            <Link
              key={item.to}
              className={active === item.to ? 'is-active' : ''}
              to={item.to}
            >
              <Icon name={item.icon} size={20} /><span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </aside>

      <main className="main-content" id="main-content" tabIndex={-1}>
        {storageError ? (
          <div className="storage-alert" role="alert">
            <span>端末への保存に失敗しました。空き容量やブラウザ設定を確認してください。</span>
            <button type="button" onClick={() => setStorageError(false)} aria-label="通知を閉じる"><Icon name="close" size={20}/></button>
          </div>
        ) : null}
        {children}
        <footer className="site-footer">
          <Link to="/terms">利用規約</Link>
          <Link to="/privacy">プライバシー・削除窓口</Link>
        </footer>
      </main>

      <nav className="bottom-nav" aria-label="mobile navigation">
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={active === item.to ? 'is-active' : ''}
          >
            <Icon name={item.icon} size={20} /><span>{item.label}</span>
          </Link>
        ))}
      </nav>
    </div>
  );
}
