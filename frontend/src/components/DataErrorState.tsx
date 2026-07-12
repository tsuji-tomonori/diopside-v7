import { ContractErrorKind } from '@/lib/contract';

const labels: Record<ContractErrorKind, string> = {
  not_found: '公開データが見つかりません。',
  timeout: '公開データの取得がタイムアウトしました。',
  server: '公開データサーバーでエラーが発生しました。',
  network: 'ネットワーク接続を確認してください。',
  schema: '公開データの形式が不正です。',
  release_mismatch: '公開データの版が一致しません。',
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
      <p>{detail}</p>
      <button type="button" onClick={retry}>再取得</button>
    </section>
  );
}
