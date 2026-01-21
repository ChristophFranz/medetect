import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const { nfc_tag_id } = await req.json()

    if (!nfc_tag_id || typeof nfc_tag_id !== 'string') {
      return new Response(
        JSON.stringify({ error: 'Invalid NFC tag ID' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate NFC tag ID format (alphanumeric, reasonable length)
    const sanitizedNfcId = nfc_tag_id.trim()
    if (sanitizedNfcId.length < 1 || sanitizedNfcId.length > 50 || !/^[a-zA-Z0-9]+$/.test(sanitizedNfcId)) {
      return new Response(
        JSON.stringify({ error: 'Invalid NFC tag ID format' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Lookup user by NFC tag - only return non-sensitive fields
    const { data, error } = await supabase
      .from('users')
      .select('id, name, role, tags')
      .eq('nfc_tag_id', sanitizedNfcId)
      .maybeSingle()

    if (error) {
      console.error('Database error:', error)
      return new Response(
        JSON.stringify({ error: 'Database error' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    if (!data) {
      return new Response(
        JSON.stringify({ error: 'User not found', found: false }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Return user data (excluding sensitive NFC tag ID)
    return new Response(
      JSON.stringify({ 
        user: {
          id: data.id,
          name: data.name,
          role: data.role,
          tags: data.tags
        },
        found: true
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (err) {
    console.error('Unexpected error:', err)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
