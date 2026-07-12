import { POLICY_LINKS } from '@/lib/policy';

export function TermsPage() {
  return (
    <article className="legal-page">
      <h1>利用規約</h1>
      <p>diopsideは公開YouTubeアーカイブを検索・再訪するための非公式サービスです。</p>
      <h2>利用データ</h2>
      <p>YouTube API Servicesから取得した公開metadataと、許可された範囲の派生成果物を表示します。動画の権利は各権利者に帰属します。</p>
      <h2>禁止事項</h2>
      <p>サービスへの過負荷、取得データの権利を侵害する再配布、不正アクセスを禁止します。</p>
      <h2>外部サービス</h2>
      <p><a href={POLICY_LINKS.youtubeTerms} target="_blank" rel="noreferrer">YouTube API Services Terms / Developer Policies</a>が適用されます。</p>
      <h2>免責・変更</h2>
      <p>公開元の削除・非公開化、API制約、保守により表示を停止する場合があります。重大変更時はpolicy major versionを更新し、再同意を求めます。</p>
    </article>
  );
}
