import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="dio-not-found-page">
      <h1 className="dio-display">ページが見つかりません</h1>
      <p>指定されたページは存在しないか、移動した可能性があります。</p>
      <div className="dio-page-actions">
        <Link className="dio-button dio-button--primary" to="/">ホームへ戻る</Link>
        <Link className="dio-button" to="/search">検索を開く</Link>
      </div>
    </section>
  );
}
