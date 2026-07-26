import { ContractErrorKind } from '@/lib/contract';
import { Button } from '@/components/ui/Button';

const labels: Record<ContractErrorKind, string> = {
  not_found: '公開データが見つかりません。',
  timeout: '公開データの取得がタイムアウトしました。',
  server: '公開データサーバーでエラーが発生しました。',
  network: 'ネットワーク接続を確認してください。',
  schema: '公開データの形式が不正です。',
  release_mismatch: '公開データの版が一致しません。',
};

const guidance: Record<ContractErrorKind, string> = {
  not_found: '必要な公開データが見つかりません。公開状況をご確認ください。',
  timeout: 'しばらく待ってから、もう一度お試しください。',
  server: '公開データサーバーで問題が発生しています。しばらく待ってから、もう一度お試しください。',
  network: '通信状況を確認してから、もう一度お試しください。',
  schema: '公開データを確認できません。時間をおいて再取得してください。',
  release_mismatch: '公開データの更新中です。しばらく待ってから、もう一度お試しください。',
};

interface Props {
  kind: ContractErrorKind;
  detail: string;
  retry: () => void;
}

export function DataErrorState({ kind, detail, retry }: Props) {
  return (
    <section className="status-card" role="alert">
      <h2>{labels[kind]}</h2>
      <p>{guidance[kind]}</p>
      <details className="dio-error-detail">
        <summary>技術情報を表示</summary>
        <p>取得時の詳細: {detail}</p>
      </details>
      <Button type="button" onClick={retry}>再取得</Button>
    </section>
  );
}
