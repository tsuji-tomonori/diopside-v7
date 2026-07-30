import { ReactNode, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { storageErrorEvent } from '@/lib/storage';
import { NavIcon } from '@/components/NavIcon';

interface AppShellProps {
  children: ReactNode;
}

const navItems = [
  { label: 'ホーム', to: '/', icon: 'home' },
  { label: '検索', to: '/search', icon: 'search' },
  { label: '保存', to: '/saved', icon: 'saved' },
  { label: '履歴', to: '/history', icon: 'history' },
] as const;

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
        <Link className="brand" to="/" aria-label="diopside ホーム">
          <span className="wordmark">diopside</span>
          <span className="brand-caption">SHIRAYUKI TOMOE ARCHIVE</span>
        </Link>
        <nav aria-label="main navigation" className="side-nav">
          {navItems.map((item) => (
            <Link
              key={item.to}
              className={active === item.to ? 'is-active' : ''}
              to={item.to}
              aria-current={active === item.to ? 'page' : undefined}
            >
              <NavIcon name={item.icon} />
              {item.label}
            </Link>
          ))}
        </nav>
        <p className="sidebar-note">
          公開アーカイブを、言葉と記憶からたどる。
        </p>
      </aside>

      <header className="mobile-topbar">
        <Link className="wordmark" to="/">diopside</Link>
        <span>白雪巴アーカイブ</span>
      </header>

      <main className="main-content" id="main-content" tabIndex={-1}>
        {storageError ? (
          <div className="storage-alert" role="alert">
            <div>
              <strong>端末に保存できませんでした</strong>
              <span>空き容量やブラウザの保存設定を確認してください。</span>
            </div>
            <button className="button button-quiet" type="button" onClick={() => setStorageError(false)}>閉じる</button>
          </div>
        ) : null}
        <div className="page-container">{children}</div>
        <footer className="site-footer">
          <Link to="/terms">利用規約</Link>
          <Link to="/privacy">プライバシー・削除窓口</Link>
          <span>非公式ファンアーカイブ</span>
        </footer>
      </main>

      <nav className="bottom-nav" aria-label="mobile navigation">
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={active === item.to ? 'is-active' : ''}
            aria-current={active === item.to ? 'page' : undefined}
          >
            <NavIcon name={item.icon} />
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
