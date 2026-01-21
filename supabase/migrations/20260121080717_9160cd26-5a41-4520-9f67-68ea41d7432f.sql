-- Create a table for inspection cases
CREATE TABLE public.inspection_cases (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  case_number SERIAL,
  patient_name TEXT NOT NULL,
  user_id UUID NOT NULL,
  user_name TEXT NOT NULL,
  folder_path TEXT NOT NULL,
  layer1_image_path TEXT,
  layer2_image_path TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.inspection_cases ENABLE ROW LEVEL SECURITY;

-- Create policies for access via edge functions (service role)
CREATE POLICY "Allow service role full access to inspection_cases"
ON public.inspection_cases
FOR ALL
USING (true)
WITH CHECK (true);

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_inspection_cases_updated_at
BEFORE UPDATE ON public.inspection_cases
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Create storage bucket for case images if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('case-images', 'case-images', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for case images
CREATE POLICY "Anyone can view case images"
ON storage.objects
FOR SELECT
USING (bucket_id = 'case-images');

CREATE POLICY "Service role can upload case images"
ON storage.objects
FOR INSERT
WITH CHECK (bucket_id = 'case-images');

CREATE POLICY "Service role can delete case images"
ON storage.objects
FOR DELETE
USING (bucket_id = 'case-images');