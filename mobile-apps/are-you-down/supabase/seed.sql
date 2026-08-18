-- Seed data for local development.
--
-- Run automatically by `supabase db reset`. Safe to re-run: everything is
-- idempotent on fixed UUIDs.
--
-- All seeded users share the password `password123`, which is only useful if
-- you swap the auth screen to password sign-in for debugging. The app itself
-- uses magic links — locally those land in Inbucket at http://127.0.0.1:54324.

-- ---------------------------------------------------------------------------
-- Schools
-- ---------------------------------------------------------------------------

insert into public.schools (id, name, email_domain) values
  ('a0000000-0000-4000-8000-000000000001', 'UC Merced',        'ucmerced.edu'),
  ('a0000000-0000-4000-8000-000000000002', 'San José State',   'sjsu.edu')
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- Users
--
-- Inserting into auth.users fires public.handle_new_user(), which derives the
-- campus from the email domain and creates the profile. That is the same path
-- a real signup takes, so the seed exercises the gating trigger too.
-- ---------------------------------------------------------------------------

do $$
declare
  u record;
begin
  for u in
    select * from (values
      -- UC Merced
      ('b0000000-0000-4000-8000-000000000001'::uuid, 'jonathan@ucmerced.edu', 'Jonathan R.'),
      ('b0000000-0000-4000-8000-000000000002'::uuid, 'maya@ucmerced.edu',     'Maya P.'),
      ('b0000000-0000-4000-8000-000000000003'::uuid, 'devon@ucmerced.edu',    'Devon K.'),
      ('b0000000-0000-4000-8000-000000000004'::uuid, 'priya@ucmerced.edu',    'Priya S.'),
      ('b0000000-0000-4000-8000-000000000005'::uuid, 'alex@ucmerced.edu',     'Alex T.'),
      ('b0000000-0000-4000-8000-000000000006'::uuid, 'sam@ucmerced.edu',      'Sam O.'),
      ('b0000000-0000-4000-8000-000000000007'::uuid, 'nina@ucmerced.edu',     'Nina B.'),
      ('b0000000-0000-4000-8000-000000000008'::uuid, 'chris@ucmerced.edu',    'Chris L.'),
      -- San José State
      ('b0000000-0000-4000-8000-000000000011'::uuid, 'ravi@sjsu.edu',         'Ravi M.'),
      ('b0000000-0000-4000-8000-000000000012'::uuid, 'jules@sjsu.edu',        'Jules W.'),
      ('b0000000-0000-4000-8000-000000000013'::uuid, 'tori@sjsu.edu',         'Tori A.'),
      ('b0000000-0000-4000-8000-000000000014'::uuid, 'omar@sjsu.edu',         'Omar H.')
    ) as t(id, email, display_name)
  loop
    insert into auth.users (
      instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
      confirmation_token, recovery_token, email_change_token_new, email_change
    ) values (
      '00000000-0000-0000-0000-000000000000',
      u.id, 'authenticated', 'authenticated', u.email,
      extensions.crypt('password123', extensions.gen_salt('bf')),
      now(),
      '{"provider":"email","providers":["email"]}'::jsonb,
      jsonb_build_object('display_name', u.display_name),
      now(), now(), '', '', '', ''
    )
    on conflict (id) do nothing;

    -- Newer GoTrue requires a matching identity row for email sign-in. Guard
    -- it so a schema drift here never takes down the whole seed.
    begin
      insert into auth.identities (
        id, user_id, provider_id, identity_data, provider,
        last_sign_in_at, created_at, updated_at
      ) values (
        gen_random_uuid(), u.id, u.id::text,
        jsonb_build_object('sub', u.id::text, 'email', u.email),
        'email', now(), now(), now()
      )
      on conflict do nothing;
    exception when others then
      raise warning 'Could not seed auth.identities for % (%)', u.email, sqlerrm;
    end;
  end loop;
end;
$$;

-- ---------------------------------------------------------------------------
-- Drops
--
-- Timestamps are relative to seed time so the feed always has fresh content.
-- The set deliberately includes two already-expired drops and one closed drop
-- so you can confirm they never reach the feed.
-- ---------------------------------------------------------------------------

insert into public.drops (id, user_id, school_id, body, category, expires_at, status, created_at) values
  -- UC Merced — live
  ('c0000000-0000-4000-8000-000000000001', 'b0000000-0000-4000-8000-000000000002', 'a0000000-0000-4000-8000-000000000001',
   'Are you down to go to Target rn? Need a fan before it hits 105 tomorrow', 'target_run',
   now() + interval '45 minutes', 'open', now() - interval '4 minutes'),

  ('c0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000003', 'a0000000-0000-4000-8000-000000000001',
   'Pav dinner in 20? I refuse to eat alone again', 'dining_hall',
   now() + interval '35 minutes', 'open', now() - interval '11 minutes'),

  ('c0000000-0000-4000-8000-000000000003', 'b0000000-0000-4000-8000-000000000004', 'a0000000-0000-4000-8000-000000000001',
   'CSE 100 midterm review in the library 3rd floor until close', 'exam_cram',
   now() + interval '3 hours', 'open', now() - interval '22 minutes'),

  ('c0000000-0000-4000-8000-000000000004', 'b0000000-0000-4000-8000-000000000005', 'a0000000-0000-4000-8000-000000000001',
   'Anyone down for a lift at the rec center? Leg day, bring your own suffering', 'workout',
   now() + interval '90 minutes', 'open', now() - interval '31 minutes'),

  ('c0000000-0000-4000-8000-000000000005', 'b0000000-0000-4000-8000-000000000006', 'a0000000-0000-4000-8000-000000000001',
   'Boba run, I have a car and questionable taste in music', 'boba',
   now() + interval '25 minutes', 'open', now() - interval '38 minutes'),

  ('c0000000-0000-4000-8000-000000000006', 'b0000000-0000-4000-8000-000000000007', 'a0000000-0000-4000-8000-000000000001',
   'Sunset walk around the lake before it gets dark', 'walk',
   now() + interval '70 minutes', 'open', now() - interval '46 minutes'),

  ('c0000000-0000-4000-8000-000000000007', 'b0000000-0000-4000-8000-000000000008', 'a0000000-0000-4000-8000-000000000001',
   'Costco run tonight, splitting a membership guest pass', 'errand',
   now() + interval '2 hours', 'open', now() - interval '55 minutes'),

  ('c0000000-0000-4000-8000-000000000008', 'b0000000-0000-4000-8000-000000000002', 'a0000000-0000-4000-8000-000000000001',
   'Study grind at the SSB lobby, headphones on, just need company', 'library',
   now() + interval '4 hours', 'open', now() - interval '68 minutes'),

  ('c0000000-0000-4000-8000-000000000009', 'b0000000-0000-4000-8000-000000000003', 'a0000000-0000-4000-8000-000000000001',
   'Pickup basketball at the courts in 30, need 2 more', 'basketball',
   now() + interval '55 minutes', 'open', now() - interval '77 minutes'),

  -- UC Merced — closed and expired (should never appear in a feed)
  ('c0000000-0000-4000-8000-000000000010', 'b0000000-0000-4000-8000-000000000004', 'a0000000-0000-4000-8000-000000000001',
   'Late night In-N-Out, first four people', 'late_night',
   now() + interval '40 minutes', 'closed', now() - interval '85 minutes'),

  ('c0000000-0000-4000-8000-000000000011', 'b0000000-0000-4000-8000-000000000005', 'a0000000-0000-4000-8000-000000000001',
   'Farmers market this morning, leaving in 10', 'groceries',
   now() - interval '3 hours', 'expired', now() - interval '6 hours'),

  ('c0000000-0000-4000-8000-000000000012', 'b0000000-0000-4000-8000-000000000006', 'a0000000-0000-4000-8000-000000000001',
   'Anyone up for coffee before my 8am', 'coffee',
   now() - interval '30 minutes', 'open', now() - interval '4 hours'),

  -- San José State — a second campus, to prove school scoping works
  ('c0000000-0000-4000-8000-000000000013', 'b0000000-0000-4000-8000-000000000011', 'a0000000-0000-4000-8000-000000000002',
   'Downtown food crawl starting at the paseo, come thru', 'food',
   now() + interval '2 hours', 'open', now() - interval '9 minutes'),

  ('c0000000-0000-4000-8000-000000000014', 'b0000000-0000-4000-8000-000000000012', 'a0000000-0000-4000-8000-000000000002',
   'Need a gym buddy for the 9pm session at the SRAC', 'workout',
   now() + interval '3 hours', 'open', now() - interval '25 minutes'),

  ('c0000000-0000-4000-8000-000000000015', 'b0000000-0000-4000-8000-000000000013', 'a0000000-0000-4000-8000-000000000002',
   'Discrete math problem set, MLK library 5th floor, misery loves company', 'study',
   now() + interval '5 hours', 'open', now() - interval '41 minutes')
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- Responses
--
-- These fire public.handle_response(), so the threads and thread_users rows
-- below are created by the real trigger rather than inserted by hand.
-- ---------------------------------------------------------------------------

insert into public.responses (drop_id, user_id, type) values
  -- Two people are down for the study session -> creates a 3-person thread
  ('c0000000-0000-4000-8000-000000000003', 'b0000000-0000-4000-8000-000000000001', 'down'),
  ('c0000000-0000-4000-8000-000000000003', 'b0000000-0000-4000-8000-000000000007', 'down'),
  -- One person down for the Target run
  ('c0000000-0000-4000-8000-000000000001', 'b0000000-0000-4000-8000-000000000008', 'down'),
  -- Passes: invisible to everyone including the author, they just filter feeds
  ('c0000000-0000-4000-8000-000000000005', 'b0000000-0000-4000-8000-000000000001', 'pass'),
  ('c0000000-0000-4000-8000-000000000009', 'b0000000-0000-4000-8000-000000000001', 'pass')
on conflict (drop_id, user_id) do nothing;

-- ---------------------------------------------------------------------------
-- Messages in the seeded study thread
-- ---------------------------------------------------------------------------

insert into public.messages (thread_id, user_id, body, created_at)
select t.id, v.user_id, v.body, now() - v.ago
from public.threads t
cross join (values
  ('b0000000-0000-4000-8000-000000000004'::uuid, 'hey! I grabbed the big table by the windows', interval '14 minutes'),
  ('b0000000-0000-4000-8000-000000000001'::uuid, 'omw, 10 min out', interval '12 minutes'),
  ('b0000000-0000-4000-8000-000000000007'::uuid, 'same, bringing the practice exam printouts', interval '9 minutes')
) as v(user_id, body, ago)
where t.drop_id = 'c0000000-0000-4000-8000-000000000003'
  and not exists (select 1 from public.messages m where m.thread_id = t.id);

-- ---------------------------------------------------------------------------
-- Safety fixtures: one block pair and one report, so the bidirectional feed
-- filter and the admin views have something to show.
-- ---------------------------------------------------------------------------

insert into public.blocks (blocker_id, blocked_id) values
  ('b0000000-0000-4000-8000-000000000001', 'b0000000-0000-4000-8000-000000000006')
on conflict (blocker_id, blocked_id) do nothing;

insert into public.reports (reporter_id, target_type, target_id, reason)
select 'b0000000-0000-4000-8000-000000000007', 'drop',
       'c0000000-0000-4000-8000-000000000010', 'Spam — reposted this five times today'
where not exists (select 1 from public.reports);

-- ---------------------------------------------------------------------------
-- Profile details, so the view screen has something to show
-- ---------------------------------------------------------------------------

update public.profiles set
  pronouns   = v.pronouns,
  class_year = v.class_year,
  major      = v.major,
  bio        = v.bio
from (values
  ('b0000000-0000-4000-8000-000000000001'::uuid, 'he/him',   'junior',    'Computer Science',
   'Mostly here for late night food runs and midterm suffering.'),
  ('b0000000-0000-4000-8000-000000000002'::uuid, 'she/her',  'sophomore', 'Bioengineering',
   'I will drive. You pick the playlist.'),
  ('b0000000-0000-4000-8000-000000000003'::uuid, 'he/him',   'senior',    'Mechanical Engineering',
   'Pav regular. Ask me about the good hours.'),
  ('b0000000-0000-4000-8000-000000000004'::uuid, 'she/her',  'junior',    'Cognitive Science',
   'Study group organiser by necessity, not choice.'),
  ('b0000000-0000-4000-8000-000000000007'::uuid, 'they/them','freshman',  'Undeclared',
   'New here. Down for almost anything once.')
) as v(id, pronouns, class_year, major, bio)
where public.profiles.id = v.id;

insert into public.profile_interests (profile_id, category_slug) values
  ('b0000000-0000-4000-8000-000000000001', 'games'),
  ('b0000000-0000-4000-8000-000000000001', 'anime'),
  ('b0000000-0000-4000-8000-000000000001', 'late_night'),
  ('b0000000-0000-4000-8000-000000000002', 'boba'),
  ('b0000000-0000-4000-8000-000000000002', 'target_run'),
  ('b0000000-0000-4000-8000-000000000003', 'basketball'),
  ('b0000000-0000-4000-8000-000000000004', 'exam_cram'),
  ('b0000000-0000-4000-8000-000000000007', 'walk'),
  ('b0000000-0000-4000-8000-000000000007', 'movie')
on conflict (profile_id, category_slug) do nothing;
