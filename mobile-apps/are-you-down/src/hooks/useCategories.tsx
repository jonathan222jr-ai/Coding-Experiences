import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { fetchCategoryMenu, type Category, type CategoryMenu } from '../api/categories';
import { NEUTRAL_TINT } from '../theme';

/** Everything a chip needs to render one category, resolved in one lookup. */
export interface CategoryDescription {
  label: string;
  emoji: string;
  /** The group's colour. Every chip for this category is tinted with it. */
  color: string;
  /** Null when the slug doesn't resolve — an unknown or retired category. */
  groupSlug: string | null;
  groupLabel: string | null;
}

interface CategoriesContextValue {
  menu: CategoryMenu | null;
  error: string | null;
  reload: () => Promise<void>;
  /** Label, emoji and group colour for a slug, with a fallback for unknown ones. */
  describe: (slug: string) => CategoryDescription;
}

const CategoriesContext = createContext<CategoriesContextValue | null>(null);

const FALLBACK: CategoryDescription = {
  label: 'Something',
  emoji: '📍',
  color: NEUTRAL_TINT,
  groupSlug: null,
  groupLabel: null,
};

/**
 * Loads the category menu once and shares it.
 *
 * Every screen needs to turn a slug into an emoji and a label, and the menu is
 * ~35 rows that change roughly never — so it is fetched once at sign-in rather
 * than joined onto every feed and thread query.
 */
export function CategoriesProvider({ children }: { children: ReactNode }) {
  const [menu, setMenu] = useState<CategoryMenu | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setMenu(await fetchCategoryMenu());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const describe = useCallback(
    (slug: string): CategoryDescription => {
      const category: Category | undefined = menu?.bySlug[slug];
      if (!category) {
        // A drop can outlive its category, and the menu may not have loaded
        // yet. Neither is worth a broken row.
        return FALLBACK;
      }

      const group = menu?.groupBySlug[category.group_slug];

      return {
        label: category.label,
        emoji: category.emoji,
        color: group?.color ?? NEUTRAL_TINT,
        groupSlug: category.group_slug,
        groupLabel: group?.label ?? null,
      };
    },
    [menu],
  );

  const value = useMemo<CategoriesContextValue>(
    () => ({ menu, error, reload, describe }),
    [menu, error, reload, describe],
  );

  return <CategoriesContext.Provider value={value}>{children}</CategoriesContext.Provider>;
}

export function useCategories(): CategoriesContextValue {
  const context = useContext(CategoriesContext);
  if (!context) {
    throw new Error('useCategories must be used inside a CategoriesProvider.');
  }
  return context;
}
