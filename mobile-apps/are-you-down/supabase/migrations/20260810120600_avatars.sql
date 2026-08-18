-- Avatar storage.
--
-- One public bucket. Files live under a folder named for the owner's user id,
-- which is what the write policies key off — you can only put things in your
-- own folder.
--
-- Reads are public: an avatar shows up next to a display name on a campus feed,
-- so signed URLs would buy nothing except expiry bugs. Nothing private is ever
-- stored here.
--
-- Wrapped in a guard because the `storage` schema comes from Supabase itself
-- and is absent from a plain Postgres, where this migration should be a no-op
-- rather than a failure.

do $$
begin
  if to_regclass('storage.objects') is null then
    raise warning 'No storage schema here; skipping avatar bucket setup.';
    return;
  end if;

  insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
  values (
    'avatars',
    'avatars',
    true,
    2097152, -- 2 MB
    array['image/jpeg', 'image/png', 'image/webp']
  )
  on conflict (id) do update
    set public             = excluded.public,
        file_size_limit    = excluded.file_size_limit,
        allowed_mime_types = excluded.allowed_mime_types;

  execute $p$drop policy if exists avatars_read on storage.objects$p$;
  execute $p$
    create policy avatars_read on storage.objects
      for select
      using (bucket_id = 'avatars')
  $p$;

  execute $p$drop policy if exists avatars_insert_own on storage.objects$p$;
  execute $p$
    create policy avatars_insert_own on storage.objects
      for insert to authenticated
      with check (
        bucket_id = 'avatars'
        and (storage.foldername(name))[1] = auth.uid()::text
      )
  $p$;

  execute $p$drop policy if exists avatars_update_own on storage.objects$p$;
  execute $p$
    create policy avatars_update_own on storage.objects
      for update to authenticated
      using (
        bucket_id = 'avatars'
        and (storage.foldername(name))[1] = auth.uid()::text
      )
  $p$;

  execute $p$drop policy if exists avatars_delete_own on storage.objects$p$;
  execute $p$
    create policy avatars_delete_own on storage.objects
      for delete to authenticated
      using (
        bucket_id = 'avatars'
        and (storage.foldername(name))[1] = auth.uid()::text
      )
  $p$;
end;
$$;
