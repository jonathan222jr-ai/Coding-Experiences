-- The one push notification this app sends: the drop's author is told when
-- somebody joins their thread. Nothing else pushes. No digests, no re-engagement
-- nudges, no "someone passed on your drop" — that last one is the whole reason
-- passes are private.

do $$
begin
  create extension if not exists pg_net;
exception when others then
  raise warning 'pg_net unavailable (%); thread-join pushes will be skipped.', sqlerrm;
end;
$$;

create or replace function public.notify_thread_join()
returns trigger
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_author_id uuid;
  v_drop_body text;
  v_joiner    text;
  v_messages  jsonb;
begin
  select d.user_id, d.body
  into v_author_id, v_drop_body
  from public.threads t
  join public.drops d on d.id = t.drop_id
  where t.id = new.thread_id;

  -- The author is seated by the same trigger that creates the thread, so the
  -- first row through here is the author themselves. Don't notify them that
  -- they joined their own hangout.
  if v_author_id is null or v_author_id = new.user_id then
    return new;
  end if;

  select p.display_name into v_joiner
  from public.profiles p
  where p.id = new.user_id;

  -- Expo accepts up to 100 message objects per request, so one call covers
  -- every device the author has signed in on.
  select jsonb_agg(
    jsonb_build_object(
      'to', pt.token,
      'title', 'Someone''s down',
      'body', coalesce(v_joiner, 'Someone') || ' is in for "' || left(v_drop_body, 60) || '"',
      'sound', 'default',
      'channelId', 'default',
      'data', jsonb_build_object('threadId', new.thread_id)
    )
  )
  into v_messages
  from public.push_tokens pt
  where pt.user_id = v_author_id;

  if v_messages is null then
    return new;
  end if;

  -- pg_net queues the request and returns immediately, so this adds no latency
  -- to the response that triggered it.
  perform net.http_post(
    url     := 'https://exp.host/--/api/v2/push/send',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Accept', 'application/json'
    ),
    body    := v_messages
  );

  return new;
exception
  when others then
    -- A failed notification must never roll back the join that caused it.
    -- Being in the thread is the thing that matters; the push is a courtesy.
    raise warning 'Thread-join push failed: %', sqlerrm;
    return new;
end;
$$;

drop trigger if exists thread_users_after_insert on public.thread_users;
create trigger thread_users_after_insert
  after insert on public.thread_users
  for each row execute function public.notify_thread_join();
