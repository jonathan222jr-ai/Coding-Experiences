-- Moderation views.
--
-- These live in a dedicated `admin` schema that is NOT exposed through the
-- PostgREST API, so they are only reachable from the SQL editor or a
-- service-role connection. No app client can read them at any privilege level
-- the app ships with.

create schema if not exists admin;

revoke all on schema admin from public, anon, authenticated;

-- Every report, resolved against whatever it points at. target_id is a plain
-- uuid rather than an FK because it can address three different tables, so
-- each subquery is left-joined by hand.
create or replace view admin.reports_detail as
select
  r.id,
  r.created_at,
  r.reason,
  r.target_type,
  r.target_id,
  reporter.display_name as reporter_name,
  reporter_school.name  as reporter_school,
  case r.target_type
    when 'drop'    then (select d.body from public.drops d where d.id = r.target_id)
    when 'message' then (select m.body from public.messages m where m.id = r.target_id)
    when 'user'    then (select p.display_name from public.profiles p where p.id = r.target_id)
  end as target_content,
  case r.target_type
    when 'drop'    then (select d.user_id from public.drops d where d.id = r.target_id)
    when 'message' then (select m.user_id from public.messages m where m.id = r.target_id)
    when 'user'    then r.target_id
  end as target_author_id
from public.reports r
join public.profiles reporter on reporter.id = r.reporter_id
join public.schools reporter_school on reporter_school.id = reporter.school_id
order by r.created_at desc;

comment on view admin.reports_detail is
  'Moderation queue. Service role / SQL editor only.';

-- Users with the most reports filed against their content, worst first.
create or replace view admin.most_reported_users as
select
  target_author_id as user_id,
  (select display_name from public.profiles p where p.id = target_author_id) as display_name,
  count(*)::int as report_count,
  max(created_at) as last_reported_at
from admin.reports_detail
where target_author_id is not null
group by target_author_id
order by count(*) desc, max(created_at) desc;
