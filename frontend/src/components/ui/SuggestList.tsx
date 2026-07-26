import { KeyboardEvent } from 'react';

export interface SuggestItem {
  id: string;
  label: string;
  detail?: string;
}

type SuggestListProps = {
  items: SuggestItem[];
  activeIndex: number;
  onSelect: (item: SuggestItem) => void;
  id?: string;
};

export function SuggestList({ items, activeIndex, onSelect, id = 'suggestions' }: SuggestListProps) {
  if (!items.length) {
    return null;
  }

  const visibleItems = items.slice(0, 4);
  const selectWithKeyboard = (event: KeyboardEvent<HTMLButtonElement>, item: SuggestItem) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(item);
    }
  };

  return (
    <ul className="dio-suggest-list" id={id} role="listbox">
      {visibleItems.map((item, index) => (
        <li aria-selected={activeIndex === index} id={`${id}-${index}`} key={item.id} role="option">
          <button
            onClick={() => onSelect(item)}
            onKeyDown={(event) => selectWithKeyboard(event, item)}
            onMouseDown={(event) => event.preventDefault()}
            type="button"
          >
            <span>{item.label}</span>
            {item.detail ? <small>{item.detail}</small> : null}
          </button>
        </li>
      ))}
    </ul>
  );
}
