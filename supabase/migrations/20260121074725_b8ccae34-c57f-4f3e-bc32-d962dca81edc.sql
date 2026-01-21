-- Create storage bucket for tool classification images
INSERT INTO storage.buckets (id, name, public)
VALUES ('tool-images', 'tool-images', true);

-- Allow authenticated users to view images
CREATE POLICY "Anyone can view tool images"
ON storage.objects FOR SELECT
USING (bucket_id = 'tool-images');

-- Allow administrators and medetect_team to upload images
CREATE POLICY "Admin and medetect_team can upload tool images"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'tool-images'
);

-- Allow administrators and medetect_team to delete images
CREATE POLICY "Admin and medetect_team can delete tool images"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'tool-images'
);