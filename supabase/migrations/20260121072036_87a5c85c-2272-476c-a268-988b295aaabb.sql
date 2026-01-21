-- =============================================
-- Security Fix: Restrict public access to users and user_roles tables
-- =============================================

-- 1. Drop overly permissive policies on users table
DROP POLICY IF EXISTS "Anyone can read users by NFC tag" ON public.users;
DROP POLICY IF EXISTS "Allow user creation" ON public.users;

-- 2. Create restrictive policies that deny direct access
-- All operations must go through Edge Functions with service role
CREATE POLICY "No direct user reads"
ON public.users
FOR SELECT
USING (false);

CREATE POLICY "No direct user inserts"
ON public.users
FOR INSERT
WITH CHECK (false);

CREATE POLICY "No direct user updates"
ON public.users
FOR UPDATE
USING (false);

CREATE POLICY "No direct user deletes"
ON public.users
FOR DELETE
USING (false);

-- 3. Fix the flawed user_roles policy
DROP POLICY IF EXISTS "Users can read own roles" ON public.user_roles;

-- Create a restrictive policy that denies public access
CREATE POLICY "No direct role reads"
ON public.user_roles
FOR SELECT
USING (false);