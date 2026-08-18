-- Richer profiles.
--
-- Every field here is optional and every one is visible to anyone on the same
-- campus. That is the whole risk model: this is an app where strangers arrange
-- to meet in person, and a photo plus a major plus a year identifies someone on
-- a campus very quickly. So the fields are deliberately few, short, and
-- structured — no free-text field long enough to hold a life story, and no
-- field that invites a phone number.
--
-- Still no location, of any kind.

alter table public.profiles
  add column bio text
    check (bio is null or char_length(bio) between 1 and 160),
  add column pronouns text
    check (pronouns is null or char_length(pronouns) between 1 and 24),
  add column major text
    check (major is null or char_length(major) between 1 and 60),
  add column class_year text
    check (class_year is null or class_year in
      ('freshman', 'sophomore', 'junior', 'senior', 'grad', 'other'));

comment on column public.profiles.bio is
  'Short, optional, campus-visible. Reportable via reports.target_type = user.';

-- class_year is a check constraint rather than a lookup table on purpose: it is
-- a genuinely fixed set of six values, unlike categories, which exist to grow.

-- ---------------------------------------------------------------------------
-- Interests
--
-- Reuses the category vocabulary rather than inventing a second one, so "into
-- anime" on a profile is the same token as an anime drop.
-- ---------------------------------------------------------------------------

create table public.profile_interests (
  profile_id    uuid not null references public.profiles (id) on delete cascade,
  category_slug text not null references public.categories (slug) on delete cascade,
  created_at    timestamptz not null default now(),
  primary key (profile_id, category_slug)
);

create index profile_interests_category_idx on public.profile_interests (category_slug);

-- Six is enough to say something and few enough that a profile stays scannable.
-- Enforced here rather than in the client for the same reason as every other
-- rule in this schema.
create or replace function public.enforce_interest_cap()
returns trigger
language plpgsql
as $$
begin
  if (
    select count(*) from public.profile_interests
    where profile_id = new.profile_id
  ) >= 6 then
    raise exception 'You can pick up to 6 interests.' using errcode = 'P0001';
  end if;

  return new;
end;
$$;

create trigger profile_interests_cap
  before insert on public.profile_interests
  for each row execute function public.enforce_interest_cap();

-- ---------------------------------------------------------------------------
-- Access
-- ---------------------------------------------------------------------------

alter table public.profile_interests enable row level security;

-- Visible to the same campus as the profile itself, so a profile and its
-- interests can never disagree about who may see them.
create policy profile_interests_select_same_school on public.profile_interests
  for select to authenticated
  using (
    exists (
      select 1 from public.profiles p
      where p.id = profile_interests.profile_id
        and (p.id = auth.uid() or p.school_id = public.current_school_id())
    )
  );

create policy profile_interests_insert_own on public.profile_interests
  for insert to authenticated
  with check (profile_id = auth.uid());

create policy profile_interests_delete_own on public.profile_interests
  for delete to authenticated
  using (profile_id = auth.uid());

grant select, insert, delete on public.profile_interests to authenticated;
