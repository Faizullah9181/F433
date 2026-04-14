import { useState, useEffect, useCallback } from "react";
import type { Paginated } from "../services/api";

interface UsePaginatedState<T> {
  items: T[];
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
  hasMore: boolean;
  total: number;
  page: number;
  pages: number;
  loadMore: () => void;
  refetch: () => void;
}

export function usePaginatedApi<T>(
  fetcher: (page: number) => Promise<Paginated<T>>,
  deps: unknown[] = []
): UsePaginatedState<T> {
  const [items, setItems] = useState<T[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dedupeById = (list: T[]): T[] => {
    const seen = new Set<string | number>();
    const out: T[] = [];

    for (const item of list) {
      const maybeObj = item as unknown as { id?: string | number };
      const key = maybeObj?.id;

      if (key == null) {
        out.push(item);
        continue;
      }

      if (seen.has(key)) continue;
      seen.add(key);
      out.push(item);
    }

    return out;
  };

  const loadPage = useCallback(async (pageNum: number, append: boolean) => {
    if (append) setLoadingMore(true);
    else setLoading(true);
    setError(null);

    try {
      const result = await fetcher(pageNum);
      setItems(prev => {
        const merged = append ? [...prev, ...result.items] : result.items;
        return dedupeById(merged);
      });
      setPage(result.page);
      setPages(result.pages);
      setTotal(result.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    setItems([]);
    setPage(1);
    loadPage(1, false);
  }, [loadPage]);

  const loadMore = useCallback(() => {
    if (page < pages && !loadingMore) {
      loadPage(page + 1, true);
    }
  }, [page, pages, loadingMore, loadPage]);

  const refetch = useCallback(() => {
    setItems([]);
    setPage(1);
    loadPage(1, false);
  }, [loadPage]);

  return {
    items,
    loading,
    loadingMore,
    error,
    hasMore: page < pages,
    total,
    page,
    pages,
    loadMore,
    refetch,
  };
}
