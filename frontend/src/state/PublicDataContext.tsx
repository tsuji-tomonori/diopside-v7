import { createContext, PropsWithChildren, useContext, useEffect, useState } from 'react';
import {
  LatestRelease,
  ReleaseIndex,
  SearchIndex,
  TagAliasIndex,
  TagTaxonomy,
  TagIndex,
} from '@/types';
import {
  ContractError,
  ContractErrorKind,
  loadLatest,
  loadReleaseIndex,
  loadSearchIndex,
  loadTags,
} from '@/lib/contract';

interface PublicDataState {
  latest: LatestRelease | null;
  release: ReleaseIndex | null;
  search: SearchIndex | null;
  taxonomy: TagTaxonomy | null;
  tagIndex: TagIndex | null;
  alias: TagAliasIndex | null;
  loading: boolean;
  error: string | null;
  errorKind: ContractErrorKind | null;
  refresh: () => Promise<void>;
}

const PublicDataContext = createContext<PublicDataState | null>(null);

export function PublicDataProvider({ children }: PropsWithChildren) {
  const [latest, setLatest] = useState<LatestRelease | null>(null);
  const [release, setRelease] = useState<ReleaseIndex | null>(null);
  const [search, setSearch] = useState<SearchIndex | null>(null);
  const [taxonomy, setTaxonomy] = useState<TagTaxonomy | null>(null);
  const [tagIndex, setTagIndex] = useState<TagIndex | null>(null);
  const [alias, setAlias] = useState<TagAliasIndex | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorKind, setErrorKind] = useState<ContractErrorKind | null>(null);

  async function refresh(): Promise<void> {
    setLoading(true);
    setError(null);
    setErrorKind(null);
    try {
      const nextLatest = await loadLatest();
      const releaseId = nextLatest.releaseId;
      const nextRelease = await loadReleaseIndex(releaseId);
      const nextSearch = await loadSearchIndex(releaseId);
      const nextTags = nextLatest.releaseMode === 'normal'
        ? await loadTags(releaseId)
        : null;
      setLatest(nextLatest);
      setRelease(nextRelease);
      setSearch(nextSearch);
      setTaxonomy(nextTags?.taxonomy ?? null);
      setTagIndex(nextTags?.index ?? null);
      setAlias(nextTags?.alias ?? null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'contract load failed';
      setError(message);
      setErrorKind(error instanceof ContractError ? error.kind : 'network');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <PublicDataContext.Provider
      value={{
        latest,
        release,
        search,
        taxonomy,
        tagIndex,
        alias,
        loading,
        error,
        errorKind,
        refresh,
      }}
    >
      {children}
    </PublicDataContext.Provider>
  );
}

export function usePublicData(): PublicDataState {
  const ctx = useContext(PublicDataContext);
  if (!ctx) {
    throw new Error('usePublicData must be used within PublicDataProvider');
  }
  return ctx;
}
