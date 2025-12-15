-- Drop the existing insert policy that doesn't work with NFC auth
DROP POLICY IF EXISTS "Admins can insert users" ON public.users;

-- Create a simpler insert policy (access control is enforced at application level)
CREATE POLICY "Allow user creation"
ON public.users
FOR INSERT
WITH CHECK (true);