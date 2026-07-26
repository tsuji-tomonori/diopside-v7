import { Chip } from './Chip';

type Condition = {
  id: string;
  label: string;
  section?: string;
};

export function ConditionRow({
  conditions,
  onOpen,
  onRemove,
}: {
  conditions: Condition[];
  onOpen: (section?: string) => void;
  onRemove: (id: string) => void;
}) {
  return (
    <div className="dio-condition-row">
      <div className="dio-condition-row__scroll">
        {conditions.length ? (
          conditions.map((condition) => (
            <Chip
              key={condition.id}
              label={condition.label}
              onClick={() => onOpen(condition.section)}
              onRemove={() => onRemove(condition.id)}
              variant="removable"
            />
          ))
        ) : (
          <>
            <Chip label="タグ" onClick={() => onOpen('tags')} variant="add" />
            <Chip label="長さ" onClick={() => onOpen('length')} variant="add" />
            <Chip label="投稿日" onClick={() => onOpen('date')} variant="add" />
          </>
        )}
        <Chip label={`条件 (${conditions.length})`} onClick={() => onOpen()} variant="action" />
      </div>
      <span className="sr-only" role="status">検索条件へ追加しました</span>
    </div>
  );
}
