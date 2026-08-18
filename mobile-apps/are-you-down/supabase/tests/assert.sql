-- Behavioural assertions against the seeded database.
-- Any failure raises and, with ON_ERROR_STOP, exits nonzero.

\set ON_ERROR_STOP on

\set u1 '''b0000000-0000-4000-8000-000000000001'''
\set u4 '''b0000000-0000-4000-8000-000000000004'''
\set u6 '''b0000000-0000-4000-8000-000000000006'''
\set u8 '''b0000000-0000-4000-8000-000000000008'''
\set u11 '''b0000000-0000-4000-8000-000000000011'''

create or replace function pg_temp.check(label text, actual anyelement, expected anyelement)
returns void language plpgsql as $$
begin
  if actual is distinct from expected then
    raise exception 'FAIL % — expected %, got %', label, expected, actual;
  end if;
  raise notice 'ok   % (%)', label, actual;
end $$;

-- Resolve thread ids up front, as superuser, into a temp table.
--
-- Looking them up later from inside a restricted role would return nothing,
-- which would make an INSERT ... SELECT silently affect zero rows and quietly
-- pass a test it never actually ran. A temp table rather than a psql variable
-- because psql does not interpolate variables inside dollar-quoted blocks.
create temp table thread_ids as
select 'c1' as label, id from public.threads
where drop_id = 'c0000000-0000-4000-8000-000000000001'
union all
select 'c3', id from public.threads
where drop_id = 'c0000000-0000-4000-8000-000000000003';

grant select on thread_ids to public;

-- ===========================================================================
-- Feed, as Jonathan (UC Merced). He has already answered c3/c5/c9 and has
-- blocked user 6.
-- ===========================================================================

set session app.current_user_id = :u1;
set role authenticated;

select pg_temp.check('feed excludes own, answered, blocked, expired, closed',
  (select count(*)::int from public.get_feed()), 6);

select pg_temp.check('feed is same-campus only',
  (select count(*)::int from public.get_feed() f
   join public.drops d on d.id = f.id
   where d.school_id <> 'a0000000-0000-4000-8000-000000000001'), 0);

select pg_temp.check('feed never returns a blocked user''s drop',
  (select count(*)::int from public.get_feed() where author_id = 'b0000000-0000-4000-8000-000000000006'), 0);

select pg_temp.check('feed is ordered newest first',
  (select bool_and(created_at >= next_created)
   from (select created_at, lead(created_at) over () as next_created
         from public.get_feed()) s
   where next_created is not null), true);

-- Keyset pagination: two pages of 3 must equal one page of 6, with no overlap.
select pg_temp.check('keyset page 1 size', (select count(*)::int from public.get_feed(3)), 3);

select pg_temp.check('keyset page 2 does not repeat page 1',
  (select count(*)::int
   from public.get_feed(3, (select created_at from public.get_feed(3) order by created_at limit 1),
                           (select id from public.get_feed(3) order by created_at limit 1)) p2
   where p2.id in (select id from public.get_feed(3))), 0);

-- Group filter. Written against whatever the seed happens to contain rather
-- than a hardcoded count, so reshuffling the seed drops can't quietly turn
-- these into assertions about nothing.
select pg_temp.check('group filter returns only that group',
  (select count(*)::int
   from public.get_feed(50, null, null, 'food') f
   join public.categories c on c.slug = f.category
   where c.group_slug <> 'food'), 0);

select pg_temp.check('group filter is a subset of the open feed',
  (select count(*)::int
   from public.get_feed(50, null, null, 'food')
   where id not in (select id from public.get_feed(50))), 0);

select pg_temp.check('the groups partition the feed',
  (select sum(n)::int from (
     select (select count(*) from public.get_feed(50, null, null, g.slug)) as n
     from public.category_groups g) s),
  (select count(*)::int from public.get_feed(50)));

-- A group nobody has posted in is an empty feed, not an unfiltered one.
select pg_temp.check('unknown group filters everything out',
  (select count(*)::int from public.get_feed(50, null, null, 'not_a_group')), 0);

-- ===========================================================================
-- RLS
-- ===========================================================================

select pg_temp.check('can only read own responses',
  (select count(*)::int from public.responses), 3);

select pg_temp.check('can only read own campus drops',
  (select count(*)::int from public.drops), 12);

select pg_temp.check('can read messages in threads I belong to',
  (select count(*)::int from public.messages), 3);

select pg_temp.check('threads list shows only mine',
  (select count(*)::int from public.get_threads()), 1);

select pg_temp.check('thread member count',
  (select member_count from public.get_threads()), 3);

select pg_temp.check('thread shows latest message',
  (select last_message_author from public.get_threads()), 'Nina B.');

select pg_temp.check('cannot read who blocked me',
  (select count(*)::int from public.blocks where blocked_id = auth.uid()), 0);

-- A pass must be invisible to the drop's author.
reset role;
set session app.current_user_id = :u4;
set role authenticated;

select pg_temp.check('author cannot see responses to their own drop',
  (select count(*)::int from public.responses
   where drop_id = 'c0000000-0000-4000-8000-000000000003'), 0);

select pg_temp.check('author sees nobody else''s responses at all',
  (select count(*)::int from public.responses), 0);

-- A non-member sees no messages.
reset role;
set session app.current_user_id = :u8;
set role authenticated;

select pg_temp.check('non-member of the study thread reads no messages',
  (select count(*)::int from public.messages), 0);

-- Writing into a thread you are not in must be refused by RLS, not just hidden
-- by the UI. user 8 is in c1's thread but not c3's.
do $$
begin
  insert into public.messages (thread_id, user_id, body)
  values ((select id from thread_ids where label = 'c3'),
          'b0000000-0000-4000-8000-000000000008', 'let me in');
  raise exception 'FAIL non-member could post into a thread';
exception when insufficient_privilege then
  raise notice 'ok   non-member cannot post into a thread';
end $$;

-- Posting as somebody else, inside a thread you are genuinely in.
do $$
begin
  insert into public.messages (thread_id, user_id, body)
  values ((select id from thread_ids where label = 'c1'),
          'b0000000-0000-4000-8000-000000000002', 'not really me');
  raise exception 'FAIL could post as another user';
exception when insufficient_privilege then
  raise notice 'ok   cannot post as another user';
end $$;

insert into public.messages (thread_id, user_id, body)
values ((select id from thread_ids where label = 'c1'),
        'b0000000-0000-4000-8000-000000000008', 'otw');

select pg_temp.check('member can post, and reads it back',
  (select count(*)::int from public.messages), 1);

-- ===========================================================================
-- Trigger rules
-- ===========================================================================

reset role;

-- Duplicate response is refused by the unique constraint.
do $$
begin
  insert into public.responses (drop_id, user_id, type)
  values ('c0000000-0000-4000-8000-000000000003', 'b0000000-0000-4000-8000-000000000001', 'down');
  raise exception 'FAIL duplicate response was allowed';
exception when unique_violation then
  raise notice 'ok   duplicate response rejected';
end $$;

-- Closed drop.
do $$
begin
  insert into public.responses (drop_id, user_id, type)
  values ('c0000000-0000-4000-8000-000000000010', 'b0000000-0000-4000-8000-000000000001', 'down');
  raise exception 'FAIL down on a closed drop was allowed';
exception when raise_exception then
  raise notice 'ok   down on closed drop rejected (%)', sqlerrm;
end $$;

-- Expired drop (status still 'open', expires_at in the past).
do $$
begin
  insert into public.responses (drop_id, user_id, type)
  values ('c0000000-0000-4000-8000-000000000012', 'b0000000-0000-4000-8000-000000000002', 'down');
  raise exception 'FAIL down on an expired drop was allowed';
exception when raise_exception then
  raise notice 'ok   down on expired drop rejected (%)', sqlerrm;
end $$;

-- Cross-campus response.
do $$
begin
  insert into public.responses (drop_id, user_id, type)
  values ('c0000000-0000-4000-8000-000000000013', 'b0000000-0000-4000-8000-000000000001', 'down');
  raise exception 'FAIL cross-campus response was allowed';
exception when insufficient_privilege then
  raise notice 'ok   cross-campus response rejected';
end $$;

-- Responding to your own drop.
do $$
begin
  insert into public.responses (drop_id, user_id, type)
  values ('c0000000-0000-4000-8000-000000000001', 'b0000000-0000-4000-8000-000000000002', 'down');
  raise exception 'FAIL self-response was allowed';
exception when insufficient_privilege then
  raise notice 'ok   self-response rejected';
end $$;

-- ---------------------------------------------------------------------------
-- Thread creation. c4 (author: user 5) has had no responses yet.
-- ---------------------------------------------------------------------------

select pg_temp.check('no thread before the first down',
  (select count(*)::int from public.threads where drop_id = 'c0000000-0000-4000-8000-000000000004'), 0);

insert into public.responses (drop_id, user_id, type)
values ('c0000000-0000-4000-8000-000000000004', 'b0000000-0000-4000-8000-000000000001', 'down');

select pg_temp.check('first down creates exactly one thread',
  (select count(*)::int from public.threads where drop_id = 'c0000000-0000-4000-8000-000000000004'), 1);

select pg_temp.check('first down seats the drop author too',
  (select count(*)::int from public.thread_users tu
   join public.threads t on t.id = tu.thread_id
   where t.drop_id = 'c0000000-0000-4000-8000-000000000004'
     and tu.user_id = 'b0000000-0000-4000-8000-000000000005'), 1);

select pg_temp.check('thread has author + responder',
  (select count(*)::int from public.thread_users tu
   join public.threads t on t.id = tu.thread_id
   where t.drop_id = 'c0000000-0000-4000-8000-000000000004'), 2);

insert into public.responses (drop_id, user_id, type)
values ('c0000000-0000-4000-8000-000000000004', 'b0000000-0000-4000-8000-000000000007', 'down');

select pg_temp.check('second down reuses the same thread',
  (select count(*)::int from public.threads where drop_id = 'c0000000-0000-4000-8000-000000000004'), 1);

select pg_temp.check('second down joins it',
  (select count(*)::int from public.thread_users tu
   join public.threads t on t.id = tu.thread_id
   where t.drop_id = 'c0000000-0000-4000-8000-000000000004'), 3);

-- A pass must never create or join a thread.
select pg_temp.check('no thread for a passed-on drop',
  (select count(*)::int from public.threads where drop_id = 'c0000000-0000-4000-8000-000000000009'), 0);

-- A pass is still accepted between blocked users (user 1 blocked user 6).
insert into public.responses (drop_id, user_id, type)
values ('c0000000-0000-4000-8000-000000000012', 'b0000000-0000-4000-8000-000000000001', 'pass');
select pg_temp.check('pass between blocked users is accepted', true, true);

-- Six-member cap: drop c2 has author user3 plus room for five.
insert into public.responses (drop_id, user_id, type) values
  ('c0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000001', 'down'),
  ('c0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000004', 'down'),
  ('c0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000005', 'down'),
  ('c0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000007', 'down'),
  ('c0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000008', 'down');

select pg_temp.check('thread filled to the cap',
  (select count(*)::int from public.thread_users tu
   join public.threads t on t.id = tu.thread_id
   where t.drop_id = 'c0000000-0000-4000-8000-000000000002'), 6);

do $$
begin
  insert into public.responses (drop_id, user_id, type)
  values ('c0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000006', 'down');
  raise exception 'FAIL seventh member was allowed';
exception when raise_exception then
  raise notice 'ok   seventh member rejected (%)', sqlerrm;
end $$;

-- ===========================================================================
-- Push notification on thread join
--
-- pg_net does not exist in this container, so http_post raises. The point of
-- these two checks is that the join still happens anyway: the notification is
-- a courtesy and must never roll back the thing it is announcing.
-- ===========================================================================

insert into public.push_tokens (user_id, token)
values ('b0000000-0000-4000-8000-000000000007', 'ExponentPushToken[test-device]');

-- user 7 authors nothing seeded, so give them a drop to be notified about.
insert into public.drops (id, user_id, school_id, body, category, expires_at)
values ('c0000000-0000-4000-8000-0000000000aa', 'b0000000-0000-4000-8000-000000000007',
        'a0000000-0000-4000-8000-000000000001', 'Anyone want to split a pizza',
        'food', now() + interval '1 hour');

insert into public.responses (drop_id, user_id, type)
values ('c0000000-0000-4000-8000-0000000000aa', 'b0000000-0000-4000-8000-000000000001', 'down');

select pg_temp.check('join succeeds even when the push backend is unavailable',
  (select count(*)::int from public.thread_users tu
   join public.threads t on t.id = tu.thread_id
   where t.drop_id = 'c0000000-0000-4000-8000-0000000000aa'), 2);

select pg_temp.check('the responder really is seated',
  (select count(*)::int from public.thread_users tu
   join public.threads t on t.id = tu.thread_id
   where t.drop_id = 'c0000000-0000-4000-8000-0000000000aa'
     and tu.user_id = 'b0000000-0000-4000-8000-000000000001'), 1);

-- ===========================================================================
-- Signup gating
-- ===========================================================================

do $$
begin
  insert into auth.users (instance_id, id, aud, role, email, created_at, updated_at)
  values ('00000000-0000-0000-0000-000000000000', gen_random_uuid(),
          'authenticated', 'authenticated', 'someone@gmail.com', now(), now());
  raise exception 'FAIL non-campus signup was allowed';
exception when invalid_parameter_value then
  raise notice 'ok   non-campus signup rejected';
end $$;

insert into auth.users (instance_id, id, aud, role, email, raw_user_meta_data, created_at, updated_at)
values ('00000000-0000-0000-0000-000000000000', 'b0000000-0000-4000-8000-0000000000ff',
        'authenticated', 'authenticated', 'newkid@ucmerced.edu',
        '{"display_name":"New Kid"}'::jsonb, now(), now());

select pg_temp.check('campus signup creates a profile on the right campus',
  (select s.name from public.profiles p join public.schools s on s.id = p.school_id
   where p.id = 'b0000000-0000-4000-8000-0000000000ff'), 'UC Merced');

select pg_temp.check('display name comes from signup metadata',
  (select display_name from public.profiles where id = 'b0000000-0000-4000-8000-0000000000ff'), 'New Kid');

-- ===========================================================================
-- Expiry sweep
-- ===========================================================================

select pg_temp.check('expire_drops sweeps the stale open drop',
  (select public.expire_drops()), 1);

select pg_temp.check('no open drops remain past their expiry',
  (select count(*)::int from public.drops where status = 'open' and expires_at < now()), 0);

-- ===========================================================================
-- Categories
-- ===========================================================================

reset role;

select pg_temp.check('category groups seeded',
  (select count(*)::int from public.category_groups), 6);

select pg_temp.check('categories seeded',
  (select count(*)::int from public.categories), 35);

select pg_temp.check('every category belongs to a real group',
  (select count(*)::int from public.categories c
   left join public.category_groups g on g.slug = c.group_slug
   where g.slug is null), 0);

select pg_temp.check('every drop resolves to a real category',
  (select count(*)::int from public.drops d
   left join public.categories c on c.slug = d.category
   where c.slug is null), 0);

-- The five original enum values survived the swap, so no drop was rewritten.
select pg_temp.check('original slugs still present',
  (select count(*)::int from public.categories
   where slug in ('food', 'errand', 'study', 'workout', 'hangout')), 5);

-- A drop cannot claim a category that does not exist.
do $$
begin
  update public.drops set category = 'underwater_basket_weaving'
  where id = 'c0000000-0000-4000-8000-000000000001';
  raise exception 'FAIL an unknown category was accepted';
exception when foreign_key_violation then
  raise notice 'ok   unknown category rejected by FK';
end $$;

-- Every group carries its own colour, and no two share one — the whole point
-- is telling groups apart at a glance in the feed.
select pg_temp.check('every group has a distinct colour',
  (select count(distinct color)::int from public.category_groups), 6);

-- The client concatenates an alpha channel onto this string. Anything that
-- isn't a six-digit hex triple would render as a transparent chip.
do $$
begin
  update public.category_groups set color = 'red' where slug = 'food';
  raise exception 'FAIL a non-hex group colour was accepted';
exception when check_violation then
  raise notice 'ok   non-hex group colour rejected';
end $$;

-- Signed-out users can read the picker menu.
set role anon;
select pg_temp.check('categories readable without a session',
  (select count(*)::int from public.categories), 35);
select pg_temp.check('group colours readable without a session',
  (select count(*)::int from public.category_groups where color is not null), 6);
reset role;

-- ===========================================================================
-- Profile fields and interests
-- ===========================================================================

reset role;
set session app.current_user_id = :u1;
set role authenticated;

select pg_temp.check('own profile detail readable',
  (select class_year from public.profiles where id = auth.uid()), 'junior');

select pg_temp.check('same-campus interests readable',
  (select count(*)::int from public.profile_interests
   where profile_id = 'b0000000-0000-4000-8000-000000000002'), 2);

-- Ravi is at SJSU; his campus must not see UC Merced interests, and vice versa.
reset role;
set session app.current_user_id = :u11;
set role authenticated;

select pg_temp.check('other-campus interests hidden',
  (select count(*)::int from public.profile_interests), 0);

-- Editing somebody else's interests must fail even though the row shape is fine.
do $$
begin
  insert into public.profile_interests (profile_id, category_slug)
  values ('b0000000-0000-4000-8000-000000000001', 'soccer');
  raise exception 'FAIL could add an interest to another profile';
exception when insufficient_privilege then
  raise notice 'ok   cannot edit another profile''s interests';
end $$;

reset role;

-- The cap is a server rule, not a client one.
--
-- Filling to the cap happens OUTSIDE the exception handler below: a plpgsql
-- block that catches an exception rolls back everything it did, so doing the
-- setup and the overflow together would silently undo the setup and leave the
-- assertion testing nothing.
insert into public.profile_interests (profile_id, category_slug)
select 'b0000000-0000-4000-8000-000000000005', slug
from public.categories
where slug <> 'karaoke'
order by slug
limit 6;

do $$
begin
  insert into public.profile_interests (profile_id, category_slug)
  values ('b0000000-0000-4000-8000-000000000005', 'karaoke');
  raise exception 'FAIL a seventh interest was allowed';
exception when raise_exception then
  raise notice 'ok   seventh interest rejected (%)', sqlerrm;
end $$;

select pg_temp.check('capped at six',
  (select count(*)::int from public.profile_interests
   where profile_id = 'b0000000-0000-4000-8000-000000000005'), 6);

-- Bad structured values are refused.
do $$
begin
  update public.profiles set class_year = 'super-senior'
  where id = 'b0000000-0000-4000-8000-000000000001';
  raise exception 'FAIL an invalid class_year was accepted';
exception when check_violation then
  raise notice 'ok   invalid class_year rejected';
end $$;

do $$
begin
  update public.profiles set bio = repeat('x', 200)
  where id = 'b0000000-0000-4000-8000-000000000001';
  raise exception 'FAIL an over-long bio was accepted';
exception when check_violation then
  raise notice 'ok   over-long bio rejected';
end $$;

-- ===========================================================================
-- Message GIFs
-- ===========================================================================

reset role;

-- A message must carry something.
do $$
begin
  insert into public.messages (thread_id, user_id, body)
  values ((select id from thread_ids where label = 'c1'),
          'b0000000-0000-4000-8000-000000000008', null);
  raise exception 'FAIL an empty message was allowed';
exception when check_violation then
  raise notice 'ok   message with neither text nor GIF rejected';
end $$;

-- The host pin is the whole security story: without it, gif_url is an
-- arbitrary URL every thread member's device will fetch.
do $$
begin
  insert into public.messages (thread_id, user_id, gif_id, gif_url, gif_preview_url)
  values ((select id from thread_ids where label = 'c1'),
          'b0000000-0000-4000-8000-000000000008',
          'evil', 'https://tracker.example.com/pixel.gif',
          'https://tracker.example.com/pixel.gif');
  raise exception 'FAIL a GIF from an arbitrary host was allowed';
exception when check_violation then
  raise notice 'ok   off-CDN gif_url rejected';
end $$;

-- A lookalike host must not slip through the pattern.
do $$
begin
  insert into public.messages (thread_id, user_id, gif_id, gif_url, gif_preview_url)
  values ((select id from thread_ids where label = 'c1'),
          'b0000000-0000-4000-8000-000000000008',
          'evil2', 'https://media.tenor.com.evil.example/x.gif',
          'https://media.tenor.com.evil.example/x.gif');
  raise exception 'FAIL a lookalike host was allowed';
exception when check_violation then
  raise notice 'ok   lookalike host rejected';
end $$;

-- A preview on the CDN does not launder a full URL that is not.
do $$
begin
  insert into public.messages (thread_id, user_id, gif_id, gif_url, gif_preview_url)
  values ((select id from thread_ids where label = 'c1'),
          'b0000000-0000-4000-8000-000000000008',
          'evil3', 'https://tracker.example.com/pixel.gif',
          'https://media.tenor.com/ok.gif');
  raise exception 'FAIL a mismatched pair was allowed';
exception when check_violation then
  raise notice 'ok   both GIF URLs are checked, not just one';
end $$;

-- Partial GIF data would render as a broken bubble.
do $$
begin
  insert into public.messages (thread_id, user_id, gif_id, gif_url)
  values ((select id from thread_ids where label = 'c1'),
          'b0000000-0000-4000-8000-000000000008',
          'partial', 'https://media.tenor.com/x.gif');
  raise exception 'FAIL a half-populated GIF was allowed';
exception when check_violation then
  raise notice 'ok   incomplete GIF rejected';
end $$;

-- The happy path: a GIF-only message, and its thread preview.
insert into public.messages (thread_id, user_id, gif_id, gif_url, gif_preview_url, gif_alt)
values ((select id from thread_ids where label = 'c1'),
        'b0000000-0000-4000-8000-000000000008',
        'abc123',
        'https://media.tenor.com/abc123/full.gif',
        'https://media1.tenor.com/abc123/tiny.gif',
        'excited dog');

select pg_temp.check('GIF-only message accepted',
  (select count(*)::int from public.messages where gif_id = 'abc123'), 1);

set session app.current_user_id = :u8;
set role authenticated;

select pg_temp.check('threads list shows a label for a GIF-only message',
  (select last_message_body from public.get_threads()
   where drop_id = 'c0000000-0000-4000-8000-000000000001'), 'GIF');

reset role;

-- ===========================================================================
-- Drop GIFs
--
-- The same pin as messages, and it matters more here: a drop is campus-wide,
-- so an off-CDN URL would be fetched by every student's device rather than by
-- the six people in a thread. Every case that is checked for messages is
-- checked again, because the two constraints are separate objects and a change
-- to one does not protect the other.
-- ===========================================================================

do $$
begin
  insert into public.drops (user_id, school_id, body, category, expires_at,
                            gif_id, gif_url, gif_preview_url)
  values ('b0000000-0000-4000-8000-000000000001',
          'a0000000-0000-4000-8000-000000000001',
          'off-CDN', 'boba', now() + interval '1 hour',
          'evil', 'https://tracker.example.com/pixel.gif',
          'https://tracker.example.com/pixel.gif');
  raise exception 'FAIL a drop GIF from an arbitrary host was allowed';
exception when check_violation then
  raise notice 'ok   off-CDN drop gif_url rejected';
end $$;

do $$
begin
  insert into public.drops (user_id, school_id, body, category, expires_at,
                            gif_id, gif_url, gif_preview_url)
  values ('b0000000-0000-4000-8000-000000000001',
          'a0000000-0000-4000-8000-000000000001',
          'lookalike', 'boba', now() + interval '1 hour',
          'evil2', 'https://media.tenor.com.evil.example/x.gif',
          'https://media.tenor.com.evil.example/x.gif');
  raise exception 'FAIL a lookalike host was allowed on a drop';
exception when check_violation then
  raise notice 'ok   lookalike host rejected on drops';
end $$;

do $$
begin
  insert into public.drops (user_id, school_id, body, category, expires_at,
                            gif_id, gif_url, gif_preview_url)
  values ('b0000000-0000-4000-8000-000000000001',
          'a0000000-0000-4000-8000-000000000001',
          'mismatched', 'boba', now() + interval '1 hour',
          'evil3', 'https://tracker.example.com/pixel.gif',
          'https://media.tenor.com/ok.gif');
  raise exception 'FAIL a mismatched pair was allowed on a drop';
exception when check_violation then
  raise notice 'ok   both drop GIF URLs are checked, not just one';
end $$;

do $$
begin
  insert into public.drops (user_id, school_id, body, category, expires_at,
                            gif_id, gif_url)
  values ('b0000000-0000-4000-8000-000000000001',
          'a0000000-0000-4000-8000-000000000001',
          'partial', 'boba', now() + interval '1 hour',
          'partial', 'https://media.tenor.com/x.gif');
  raise exception 'FAIL a half-populated drop GIF was allowed';
exception when check_violation then
  raise notice 'ok   incomplete drop GIF rejected';
end $$;

-- Unlike a message, a drop cannot be GIF-only: it is still a sentence and a
-- timer, and everything that reads a drop's text depends on that.
do $$
begin
  insert into public.drops (user_id, school_id, body, category, expires_at,
                            gif_id, gif_url, gif_preview_url)
  values ('b0000000-0000-4000-8000-000000000001',
          'a0000000-0000-4000-8000-000000000001',
          null, 'boba', now() + interval '1 hour',
          'nobody', 'https://media.tenor.com/n/full.gif',
          'https://media1.tenor.com/n/tiny.gif');
  raise exception 'FAIL a GIF-only drop was allowed';
exception when not_null_violation then
  raise notice 'ok   GIF-only drop rejected — a drop is still a sentence';
end $$;

-- The happy path, and the feed has to carry it through.
insert into public.drops (id, user_id, school_id, body, category, expires_at,
                          gif_id, gif_url, gif_preview_url, gif_width, gif_height, gif_alt)
values ('c0000000-0000-4000-8000-0000000000f1',
        'b0000000-0000-4000-8000-000000000002',
        'a0000000-0000-4000-8000-000000000001',
        'Boba and a bad movie', 'boba', now() + interval '1 hour',
        'gif123',
        'https://media.tenor.com/gif123/full.gif',
        'https://media1.tenor.com/gif123/tiny.gif',
        498, 280, 'excited cat');

set session app.current_user_id = :u1;
set role authenticated;

select pg_temp.check('the feed carries a drop GIF',
  (select gif_url from public.get_feed(50)
   where id = 'c0000000-0000-4000-8000-0000000000f1'),
  'https://media.tenor.com/gif123/full.gif');

select pg_temp.check('the feed carries the GIF dimensions',
  (select gif_width from public.get_feed(50)
   where id = 'c0000000-0000-4000-8000-0000000000f1'), 498);

reset role;

-- The preview size exists for the picker's grid; a card shows the full GIF, so
-- the feed has no reason to hand the client a second URL.
select pg_temp.check('the feed does not return gif_preview_url',
  (select position('gif_preview_url' in pg_get_function_result(oid))::int
   from pg_proc where proname = 'get_feed'), 0);

-- ===========================================================================
-- Report abuse limits and triage
-- ===========================================================================

reset role;

select pg_temp.check('seeded report starts pending',
  (select status from public.reports limit 1), 'pending');

select pg_temp.check('AI columns start empty',
  (select count(*)::int from public.reports where ai_verdict is not null), 0);

-- The same person cannot report the same thing twice to inflate its rank.
do $$
begin
  insert into public.reports (reporter_id, target_type, target_id, reason)
  values ('b0000000-0000-4000-8000-000000000007', 'drop',
          'c0000000-0000-4000-8000-000000000010', 'again');
  raise exception 'FAIL duplicate report was allowed';
exception when unique_violation then
  raise notice 'ok   duplicate report rejected';
end $$;

-- Ten an hour, then the eleventh is refused. Setup runs outside the handler
-- so the exception cannot roll it back.
insert into public.reports (reporter_id, target_type, target_id, reason)
select 'b0000000-0000-4000-8000-000000000008', 'drop', d.id, 'spam test'
from public.drops d
order by d.id
limit 10;

do $$
begin
  insert into public.reports (reporter_id, target_type, target_id, reason)
  values ('b0000000-0000-4000-8000-000000000008', 'user',
          'b0000000-0000-4000-8000-000000000002', 'one too many');
  raise exception 'FAIL report rate limit did not fire';
exception when raise_exception then
  raise notice 'ok   report rate limit fired (%)', sqlerrm;
end $$;

select pg_temp.check('rate limit capped the reporter at ten',
  (select count(*)::int from public.reports
   where reporter_id = 'b0000000-0000-4000-8000-000000000008'), 10);

-- Verdicts are constrained; a typo cannot silently become a category.
do $$
begin
  update public.reports set ai_verdict = 'definitely_bad'
  where id = (select id from public.reports limit 1);
  raise exception 'FAIL an unknown ai_verdict was accepted';
exception when check_violation then
  raise notice 'ok   unknown ai_verdict rejected';
end $$;

do $$
begin
  update public.reports set ai_confidence = 1.5
  where id = (select id from public.reports limit 1);
  raise exception 'FAIL an out-of-range confidence was accepted';
exception when check_violation then
  raise notice 'ok   out-of-range confidence rejected';
end $$;

-- Reports stay write-only from the client even with the new columns.
set session app.current_user_id = :u1;
set role authenticated;

-- Refused by the GRANT, before RLS is even consulted — the stronger of the
-- two layers, and the reason both exist.
do $$
declare v_n int;
begin
  select count(*) into v_n from public.reports;
  raise exception 'FAIL a user could read reports (% rows)', v_n;
exception when insufficient_privilege then
  raise notice 'ok   reports unreadable by users (no SELECT grant)';
end $$;

do $$
begin
  update public.reports set status = 'dismissed';
  raise exception 'FAIL a user could resolve their own report';
exception when insufficient_privilege then
  raise notice 'ok   users cannot change report status';
end $$;

reset role;

-- Untriaged reports must not sort to the bottom of the queue behind triaged
-- ones — an unreviewed report is not a low-priority report.
update public.reports
set status = 'triaged', ai_verdict = 'likely_fine', ai_confidence = 0.9
where id = (select id from public.reports order by created_at limit 1);

select pg_temp.check('untriaged outranks likely_fine in the queue',
  (select ai_verdict is null from admin.moderation_queue limit 1), true);

-- ===========================================================================
-- Admin views
-- ===========================================================================

select pg_temp.check('admin report view resolves target content',
  (select target_content from admin.reports_detail
   where target_id = 'c0000000-0000-4000-8000-000000000010'
     and target_type = 'drop'
   limit 1),
  'Late night In-N-Out, first four people');

\echo 'ALL ASSERTIONS PASSED'
