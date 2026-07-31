import { POLICY_LINKS } from '@/lib/policy';

export function PrivacyPage() {
  return (
    <article className="legal-page">
      <h1>プライバシーポリシー</h1>
      <p>保存、履歴、最近の検索、同意状態はversion付きlocalStorageへ保存され、サーバーへ送信しません。</p>
      <h2>YouTube API Services</h2>
      <p>公開動画metadata、公開chat/commentを規約と承認範囲内で処理します。author identifierや個別本文、個別支払額を公開成果物へ含めません。</p>
      <p><a href={POLICY_LINKS.youtubePrivacy} target="_blank" rel="noreferrer">Google Privacy Policy</a></p>
      <h2>保持と削除</h2>
      <p>非認可API Dataと公式live chatは原則30日以内に再取得または削除します。公開旧版は最大90日、個人を含まない運用記録は最大400日保持します。</p>
      <h2>削除・問い合わせ窓口</h2>
      <p><a href="https://github.com/tsuji-tomonori/diopside-v7/issues/new" target="_blank" rel="noreferrer">GitHub Issueで削除・訂正を依頼</a></p>
      <p>依頼対象、URL、理由を記載してください。公開情報に個人情報やcredentialを書かないでください。</p>
    </article>
  );
}
