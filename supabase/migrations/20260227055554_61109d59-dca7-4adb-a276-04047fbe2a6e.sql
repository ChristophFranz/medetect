ALTER TABLE public.inspection_cases
ADD COLUMN confirmed_by_users text[] DEFAULT '{}'::text[];