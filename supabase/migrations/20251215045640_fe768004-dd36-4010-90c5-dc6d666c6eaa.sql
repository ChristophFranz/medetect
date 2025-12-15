-- Create enum for app roles
CREATE TYPE public.app_role AS ENUM ('admin', 'user');

-- Create user_roles table
CREATE TABLE public.user_roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    role app_role NOT NULL,
    UNIQUE (user_id, role)
);

-- Enable RLS
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- Create security definer function to check roles
CREATE OR REPLACE FUNCTION public.has_role(_user_id uuid, _role app_role)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.user_roles
    WHERE user_id = _user_id
      AND role = _role
  )
$$;

-- Policy: Users can read their own roles
CREATE POLICY "Users can read own roles"
ON public.user_roles
FOR SELECT
USING (auth.uid() = user_id OR user_id IN (SELECT id FROM public.users WHERE id = user_id));

-- Policy: Allow reading roles for authenticated users checking permissions
CREATE POLICY "Anyone can check roles"
ON public.user_roles
FOR SELECT
USING (true);

-- Insert new user SNEC
INSERT INTO public.users (nfc_tag_id, name, department, role)
VALUES ('3755317397', 'SNEC', 'Administrators', 'Admin');

-- Grant admin role to SNEC user
INSERT INTO public.user_roles (user_id, role)
SELECT id, 'admin'::app_role FROM public.users WHERE nfc_tag_id = '3755317397';