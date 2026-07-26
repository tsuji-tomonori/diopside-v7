import { FormEvent, KeyboardEvent } from 'react';

import { Icon } from './Icon';

export interface SearchToken {
  id: string;
  label: string;
  description?: string;
}

type SearchBarProps = {
  query: string;
  tokens?: SearchToken[];
  suggestionsOpen?: boolean;
  suggestionListId?: string;
  activeSuggestionId?: string;
  onQueryChange: (value: string) => void;
  onTokenRemove?: (id: string) => void;
  onKeyDown?: (event: KeyboardEvent<HTMLInputElement>) => void;
  onSubmit?: (event: FormEvent<HTMLFormElement>) => void;
};

export function SearchBar({
  query,
  tokens = [],
  suggestionsOpen = false,
  suggestionListId = 'suggestions',
  activeSuggestionId,
  onQueryChange,
  onTokenRemove,
  onKeyDown,
  onSubmit,
}: SearchBarProps) {
  return (
    <form className="dio-search-bar" onSubmit={onSubmit}>
      <Icon name="search" size={20} />
      <div className="dio-search-tokens">
        {tokens.map((token) => (
          <span className="dio-search-token" key={token.id}>
            <Icon name="sell" size={16} />
            {token.label}
            <button
              aria-label={`${token.label}の条件を解除`}
              onClick={() => onTokenRemove?.(token.id)}
              type="button"
            >
              <Icon name="close" size={16} />
            </button>
          </span>
        ))}
      </div>
      <input
        aria-activedescendant={suggestionsOpen ? activeSuggestionId : undefined}
        aria-autocomplete="list"
        aria-controls={suggestionListId}
        aria-expanded={suggestionsOpen}
        aria-label="キーワード"
        onChange={(event) => onQueryChange(event.target.value)}
        onKeyDown={onKeyDown}
        placeholder="キーワード・タグ・話し言葉で検索"
        role="combobox"
        value={query}
      />
    </form>
  );
}
