/**
 * Database types.
 *
 * Hand-maintained to mirror supabase/migrations. Regenerate with:
 *   npx supabase gen types typescript --local > src/types/database.ts
 * and re-check it in whenever a migration lands.
 *
 * The `Relationships` and `CompositeTypes` members look like noise but are
 * load-bearing: supabase-js only resolves query result and update types if the
 * schema satisfies its GenericSchema constraint, and silently degrades to
 * `never` if it doesn't.
 */

/**
 * A category slug. Deliberately a plain string rather than a union: categories
 * live in the `categories` table so they can be added without shipping an app
 * release, which a compile-time union would defeat.
 */
export type DropCategory = string;
export type DropStatus = 'open' | 'closed' | 'expired';
export type ResponseType = 'down' | 'pass';
export type ReportTarget = 'drop' | 'message' | 'user';

export interface Database {
  public: {
    Tables: {
      schools: {
        Row: {
          id: string;
          name: string;
          email_domain: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          email_domain: string;
          created_at?: string;
        };
        Update: {
          name?: string;
          email_domain?: string;
        };
        Relationships: [];
      };
      profiles: {
        Row: {
          id: string;
          school_id: string;
          display_name: string;
          avatar_url: string | null;
          bio: string | null;
          pronouns: string | null;
          major: string | null;
          class_year: string | null;
          created_at: string;
        };
        Insert: {
          id: string;
          school_id: string;
          display_name: string;
          avatar_url?: string | null;
          created_at?: string;
        };
        Update: {
          display_name?: string;
          avatar_url?: string | null;
          bio?: string | null;
          pronouns?: string | null;
          major?: string | null;
          class_year?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: 'profiles_school_id_fkey';
            columns: ['school_id'];
            isOneToOne: false;
            referencedRelation: 'schools';
            referencedColumns: ['id'];
          },
        ];
      };
      drops: {
        Row: {
          id: string;
          user_id: string;
          school_id: string;
          body: string;
          category: DropCategory;
          expires_at: string;
          status: DropStatus;
          created_at: string;
          gif_id: string | null;
          gif_url: string | null;
          gif_preview_url: string | null;
          gif_width: number | null;
          gif_height: number | null;
          gif_alt: string | null;
        };
        Insert: {
          id?: string;
          user_id: string;
          school_id: string;
          body: string;
          category: DropCategory;
          expires_at: string;
          status?: DropStatus;
          created_at?: string;
          gif_id?: string | null;
          gif_url?: string | null;
          gif_preview_url?: string | null;
          gif_width?: number | null;
          gif_height?: number | null;
          gif_alt?: string | null;
        };
        Update: {
          body?: string;
          category?: DropCategory;
          expires_at?: string;
          status?: DropStatus;
        };
        Relationships: [
          {
            foreignKeyName: 'drops_user_id_fkey';
            columns: ['user_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'drops_school_id_fkey';
            columns: ['school_id'];
            isOneToOne: false;
            referencedRelation: 'schools';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'drops_category_fkey';
            columns: ['category'];
            isOneToOne: false;
            referencedRelation: 'categories';
            referencedColumns: ['slug'];
          },
        ];
      };
      responses: {
        Row: {
          id: string;
          drop_id: string;
          user_id: string;
          type: ResponseType;
          created_at: string;
        };
        Insert: {
          id?: string;
          drop_id: string;
          user_id: string;
          type: ResponseType;
          created_at?: string;
        };
        // No UPDATE policy exists for responses; an answer is final.
        Update: Record<string, never>;
        Relationships: [
          {
            foreignKeyName: 'responses_drop_id_fkey';
            columns: ['drop_id'];
            isOneToOne: false;
            referencedRelation: 'drops';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'responses_user_id_fkey';
            columns: ['user_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
        ];
      };
      threads: {
        Row: {
          id: string;
          drop_id: string;
          created_at: string;
        };
        // Written only by the response trigger.
        Insert: Record<string, never>;
        Update: Record<string, never>;
        Relationships: [
          {
            foreignKeyName: 'threads_drop_id_fkey';
            columns: ['drop_id'];
            isOneToOne: true;
            referencedRelation: 'drops';
            referencedColumns: ['id'];
          },
        ];
      };
      thread_users: {
        Row: {
          id: string;
          thread_id: string;
          user_id: string;
          joined_at: string;
        };
        // Written only by the response trigger.
        Insert: Record<string, never>;
        Update: Record<string, never>;
        Relationships: [
          {
            foreignKeyName: 'thread_users_thread_id_fkey';
            columns: ['thread_id'];
            isOneToOne: false;
            referencedRelation: 'threads';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'thread_users_user_id_fkey';
            columns: ['user_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
        ];
      };
      messages: {
        Row: {
          id: string;
          thread_id: string;
          user_id: string;
          body: string | null;
          gif_id: string | null;
          gif_url: string | null;
          gif_preview_url: string | null;
          gif_width: number | null;
          gif_height: number | null;
          gif_alt: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          thread_id: string;
          user_id: string;
          body?: string | null;
          gif_id?: string | null;
          gif_url?: string | null;
          gif_preview_url?: string | null;
          gif_width?: number | null;
          gif_height?: number | null;
          gif_alt?: string | null;
          created_at?: string;
        };
        Update: Record<string, never>;
        Relationships: [
          {
            foreignKeyName: 'messages_thread_id_fkey';
            columns: ['thread_id'];
            isOneToOne: false;
            referencedRelation: 'threads';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'messages_user_id_fkey';
            columns: ['user_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
        ];
      };
      blocks: {
        Row: {
          id: string;
          blocker_id: string;
          blocked_id: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          blocker_id: string;
          blocked_id: string;
          created_at?: string;
        };
        Update: Record<string, never>;
        Relationships: [
          {
            foreignKeyName: 'blocks_blocker_id_fkey';
            columns: ['blocker_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'blocks_blocked_id_fkey';
            columns: ['blocked_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
        ];
      };
      reports: {
        Row: {
          id: string;
          reporter_id: string;
          target_type: ReportTarget;
          target_id: string;
          reason: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          reporter_id: string;
          target_type: ReportTarget;
          target_id: string;
          reason: string;
          created_at?: string;
        };
        Update: Record<string, never>;
        Relationships: [
          {
            foreignKeyName: 'reports_reporter_id_fkey';
            columns: ['reporter_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
        ];
      };
      category_groups: {
        Row: {
          slug: string;
          label: string;
          sort_order: number;
          /** Six-digit hex, enforced by a CHECK so the client can append alpha. */
          color: string;
        };
        Insert: {
          slug: string;
          label: string;
          sort_order?: number;
          color?: string;
        };
        Update: {
          label?: string;
          sort_order?: number;
          color?: string;
        };
        Relationships: [];
      };
      profile_interests: {
        Row: {
          profile_id: string;
          category_slug: string;
          created_at: string;
        };
        Insert: {
          profile_id: string;
          category_slug: string;
          created_at?: string;
        };
        Update: Record<string, never>;
        Relationships: [
          {
            foreignKeyName: 'profile_interests_profile_id_fkey';
            columns: ['profile_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'profile_interests_category_slug_fkey';
            columns: ['category_slug'];
            isOneToOne: false;
            referencedRelation: 'categories';
            referencedColumns: ['slug'];
          },
        ];
      };
      categories: {
        Row: {
          slug: string;
          label: string;
          emoji: string;
          group_slug: string;
          sort_order: number;
          active: boolean;
        };
        Insert: {
          slug: string;
          label: string;
          emoji: string;
          group_slug: string;
          sort_order?: number;
          active?: boolean;
        };
        Update: {
          label?: string;
          emoji?: string;
          group_slug?: string;
          sort_order?: number;
          active?: boolean;
        };
        Relationships: [
          {
            foreignKeyName: 'categories_group_slug_fkey';
            columns: ['group_slug'];
            isOneToOne: false;
            referencedRelation: 'category_groups';
            referencedColumns: ['slug'];
          },
        ];
      };
      push_tokens: {
        Row: {
          user_id: string;
          token: string;
          updated_at: string;
        };
        Insert: {
          user_id: string;
          token: string;
          updated_at?: string;
        };
        Update: {
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'push_tokens_user_id_fkey';
            columns: ['user_id'];
            isOneToOne: false;
            referencedRelation: 'profiles';
            referencedColumns: ['id'];
          },
        ];
      };
    };
    Views: Record<never, never>;
    Functions: {
      get_feed: {
        Args: {
          p_limit?: number;
          p_before_created_at?: string | null;
          p_before_id?: string | null;
          /** Category group slug, or null for everything. */
          p_group?: string | null;
        };
        Returns: {
          id: string;
          body: string;
          category: DropCategory;
          expires_at: string;
          created_at: string;
          author_id: string;
          display_name: string;
          avatar_url: string | null;
          gif_url: string | null;
          gif_width: number | null;
          gif_height: number | null;
          gif_alt: string | null;
        }[];
      };
      get_threads: {
        Args: Record<never, never>;
        Returns: {
          thread_id: string;
          drop_id: string;
          drop_body: string;
          drop_category: DropCategory;
          drop_status: DropStatus;
          drop_author_id: string;
          member_count: number;
          last_message_body: string | null;
          last_message_at: string | null;
          last_message_author: string | null;
        }[];
      };
    };
    Enums: {
      drop_status: DropStatus;
      response_type: ResponseType;
      report_target: ReportTarget;
    };
    CompositeTypes: Record<never, never>;
  };
}

export type Tables<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Row'];

export type FeedRow = Database['public']['Functions']['get_feed']['Returns'][number];
export type ThreadRow = Database['public']['Functions']['get_threads']['Returns'][number];
