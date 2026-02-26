
ALTER TABLE public.inspection_cases
ADD COLUMN layer1_report jsonb DEFAULT NULL,
ADD COLUMN layer2_report jsonb DEFAULT NULL;
