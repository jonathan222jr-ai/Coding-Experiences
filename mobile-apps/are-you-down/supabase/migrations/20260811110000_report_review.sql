-- Report triage.
--
-- The AI does not decide anything. It reads a report, says how likely it is to
-- be a real violation and why, and writes that onto the row — a sort order for
-- the human queue, not a verdict. Nothing is hidden, removed, or actioned
-- without a person.
--
-- That constraint is deliberate. A model that auto-hides content turns a
-- misclassification into silent censorship, and turns coordinated false
-- reporting into a working griefing tool on a campus where everyone can see
-- everyone. Ranking is useful; punishing is not.

-- ---------------------------------------------------------------------------
-- Abuse limits — the actual attack surface today
-- ---------------------------------------------------------------------------

-- One report per person per thing. Without this, the same user can report the
-- same drop fifty times and inflate it to the top of any queue.
alter table public.reports
  add constraint reports_one_per_target unique (reporter_id, target_type, target_id);

create or replace function public.enforce_report_limits()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_recent int;
begin
  select count(*) into v_recent
  from public.reports
  where reporter_id = new.reporter_id
    and created_at > now() - interval '1 hour';

  -- Ten an hour is far above honest use and far below what it takes to bury
  -- the queue or run up an inference bill.
  if v_recent >= 10 then
    raise exception 'You have sent a lot of reports recently. We are looking at them.'
      using errcode = 'P0001';
  end if;

  return new;
end;
$$;

create trigger reports_rate_limit
  before insert on public.reports
  for each row execute function public.enforce_report_limits();

-- ---------------------------------------------------------------------------
-- Review state
--
-- Text + check constraints rather than enums: these vocabularies will move as
-- the prompt is tuned, and ALTER TYPE ... ADD VALUE cannot be used in the same
-- transaction that adds it. Same reasoning as the categories table.
-- ---------------------------------------------------------------------------

alter table public.reports
  add column status text not null default 'pending'
    check (status in ('pending', 'triaged', 'actioned', 'dismissed')),
  add column ai_verdict text
    check (ai_verdict is null or ai_verdict in
      ('likely_violation', 'unclear', 'likely_fine', 'error')),
  add column ai_confidence numeric(3, 2)
    check (ai_confidence is null or ai_confidence between 0 and 1),
  add column ai_reason text,
  add column ai_categories text[],
  add column ai_model text,
  add column triaged_at timestamptz,
  add column resolved_by uuid references public.profiles (id) on delete set null,
  add column resolved_at timestamptz,
  add column moderator_note text;

-- The queue is read in triage order, so index what orders it.
create index reports_triage_idx
  on public.reports (status, ai_verdict, ai_confidence desc, created_at);

comment on column public.reports.ai_verdict is
  'Advisory only. Nothing in this app acts on this column without a human.';

-- ---------------------------------------------------------------------------
-- Dispatch
--
-- An AFTER INSERT trigger hands the report id to the moderate-report Edge
-- Function, which does the model call. The DB never holds an Anthropic key.
--
-- If the config is absent the report simply stays 'pending' and a human works
-- it — exactly as it did before this migration. The AI is an accelerator for
-- the queue, never a prerequisite for it.
-- ---------------------------------------------------------------------------

create or replace function public.queue_report_review()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_url    text;
  v_secret text;
begin
  begin
    select decrypted_secret into v_url
    from vault.decrypted_secrets where name = 'moderation_function_url';

    select decrypted_secret into v_secret
    from vault.decrypted_secrets where name = 'moderation_shared_secret';
  exception when others then
    -- No vault (local plain Postgres) — nothing to do.
    return new;
  end;

  if v_url is null or v_secret is null then
    return new;
  end if;

  begin
    perform net.http_post(
      url     := v_url,
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'x-moderation-secret', v_secret
      ),
      body    := jsonb_build_object('report_id', new.id)
    );
  exception when others then
    -- A failed dispatch must never roll back the report itself. Same rule as
    -- the push notification: the record is what matters, the extra is extra.
    raise warning 'Could not queue report % for review: %', new.id, sqlerrm;
  end;

  return new;
end;
$$;

create trigger reports_queue_review
  after insert on public.reports
  for each row execute function public.queue_report_review();

-- ---------------------------------------------------------------------------
-- Moderation queue
-- ---------------------------------------------------------------------------

drop view if exists admin.most_reported_users;
drop view if exists admin.reports_detail;

create or replace view admin.reports_detail as
select
  r.id,
  r.created_at,
  r.status,
  r.reason,
  r.target_type,
  r.target_id,
  r.ai_verdict,
  r.ai_confidence,
  r.ai_reason,
  r.ai_categories,
  r.ai_model,
  r.triaged_at,
  r.moderator_note,
  r.resolved_at,
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
join public.schools reporter_school on reporter_school.id = reporter.school_id;

comment on view admin.reports_detail is
  'Moderation queue. Service role / SQL editor only.';

-- What a moderator actually opens: unresolved reports, worst first, with the
-- AI's reasoning attached as context rather than as a decision.
create or replace view admin.moderation_queue as
select *
from admin.reports_detail
where status in ('pending', 'triaged')
order by
  case ai_verdict
    when 'likely_violation' then 0
    when 'unclear'          then 1
    when 'error'            then 2
    when 'likely_fine'      then 3
    else 1   -- not yet triaged sorts with 'unclear', never last
  end,
  ai_confidence desc nulls last,
  created_at;

create or replace view admin.most_reported_users as
select
  target_author_id as user_id,
  (select display_name from public.profiles p where p.id = target_author_id) as display_name,
  count(*)::int as report_count,
  count(*) filter (where ai_verdict = 'likely_violation')::int as likely_violation_count,
  max(created_at) as last_reported_at
from admin.reports_detail
where target_author_id is not null
group by target_author_id
order by count(*) filter (where ai_verdict = 'likely_violation') desc, count(*) desc;
