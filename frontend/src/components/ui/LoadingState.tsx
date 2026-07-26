export function LoadingState({ label = '読み込んでいます…' }: { label?: string }) {
  return (
    <div className="dio-loading-state" role="status">
      <span className="sr-only">{label}</span>
      <i />
      <i />
      <i />
    </div>
  );
}
