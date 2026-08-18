import { supabase } from '../lib/supabase';
import type { Tables } from '../types/database';
import { toApiError } from './errors';

export type Category = Tables<'categories'>;
export type CategoryGroup = Tables<'category_groups'>;

export interface CategoryMenu {
  groups: CategoryGroup[];
  /** Active categories only, in picker order, keyed by group slug. */
  byGroup: Record<string, Category[]>;
  /** Every category including retired ones, so old drops still render. */
  bySlug: Record<string, Category>;
  /** Every group, including any whose categories are all retired. */
  groupBySlug: Record<string, CategoryGroup>;
}

/**
 * The whole category menu in one round trip.
 *
 * Labels and emoji live in the database rather than the bundle, so adding a
 * category is an INSERT — no migration, no app release. That only pays off if
 * the client never hardcodes the list, hence this.
 */
export async function fetchCategoryMenu(): Promise<CategoryMenu> {
  const [categoryResult, groupResult] = await Promise.all([
    supabase.from('categories').select('*').order('sort_order'),
    supabase.from('category_groups').select('*').order('sort_order'),
  ]);

  if (categoryResult.error) {
    throw toApiError(categoryResult.error, 'Could not load categories.');
  }

  if (groupResult.error) {
    throw toApiError(groupResult.error, 'Could not load categories.');
  }

  const categories = categoryResult.data ?? [];

  const byGroup: Record<string, Category[]> = {};
  const bySlug: Record<string, Category> = {};

  for (const category of categories) {
    bySlug[category.slug] = category;

    // Retired categories stay resolvable by slug but drop out of the picker.
    if (category.active) {
      (byGroup[category.group_slug] ??= []).push(category);
    }
  }

  const allGroups = groupResult.data ?? [];
  const groupBySlug: Record<string, CategoryGroup> = {};

  for (const group of allGroups) {
    // Keyed by every group, not just the pickable ones — a drop in a group
    // whose categories were all retired still has to resolve a colour.
    groupBySlug[group.slug] = group;
  }

  return {
    groups: allGroups.filter((group) => byGroup[group.slug]?.length),
    byGroup,
    bySlug,
    groupBySlug,
  };
}
