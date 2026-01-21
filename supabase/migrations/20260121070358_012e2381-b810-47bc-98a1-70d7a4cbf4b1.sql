-- Drop the overly permissive policy that exposes user roles publicly
DROP POLICY IF EXISTS "Anyone can check roles" ON public.user_roles;

-- The existing "Users can read own roles" policy remains, but since this app uses NFC-based
-- authentication (not Supabase Auth), we need to rely on the has_role security definer function
-- for internal role checks instead of direct table access