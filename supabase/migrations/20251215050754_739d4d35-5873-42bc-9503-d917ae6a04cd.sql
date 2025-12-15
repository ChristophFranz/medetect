-- Create enum for user tags
CREATE TYPE public.user_tag AS ENUM ('medetect_team', 'nurses', 'administrator');

-- Add tags column to users table (array of tags)
ALTER TABLE public.users ADD COLUMN tags user_tag[] DEFAULT '{}';

-- Remove old department column
ALTER TABLE public.users DROP COLUMN IF EXISTS department;

-- Update existing users with appropriate tags
UPDATE public.users SET tags = ARRAY['nurses']::user_tag[] WHERE name = 'Jason';
UPDATE public.users SET tags = ARRAY['administrator']::user_tag[] WHERE name = 'SNEC';

-- Create function to check if user has a specific tag
CREATE OR REPLACE FUNCTION public.has_tag(_user_id uuid, _tag user_tag)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.users
    WHERE id = _user_id
      AND _tag = ANY(tags)
  )
$$;

-- Allow authenticated users to insert new users (for admin user creation)
CREATE POLICY "Admins can insert users"
ON public.users
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.users u
    WHERE u.nfc_tag_id = current_setting('request.headers', true)::json->>'x-user-nfc'
    AND 'administrator' = ANY(u.tags)
  )
  OR
  EXISTS (
    SELECT 1 FROM public.users u
    WHERE u.nfc_tag_id = current_setting('request.headers', true)::json->>'x-user-nfc'
    AND 'medetect_team' = ANY(u.tags)
  )
);