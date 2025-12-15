-- Create users table for NFC tag mappings
CREATE TABLE public.users (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  nfc_tag_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  role TEXT,
  department TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access (NFC lookup doesn't require auth)
CREATE POLICY "Anyone can read users by NFC tag" 
ON public.users 
FOR SELECT 
USING (true);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Insert sample users for testing
INSERT INTO public.users (nfc_tag_id, name, role, department) VALUES
  ('12345', 'Dr. Sarah Chen', 'Senior Inspector', 'Quality Assurance'),
  ('67890', 'John Smith', 'Lab Technician', 'Research & Development'),
  ('11111', 'Emily Johnson', 'Quality Manager', 'Quality Assurance');