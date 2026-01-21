import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

type UserTag = 'medetect_team' | 'nurses' | 'administrator'

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const { requesting_user_id, nfc_tag_id, name, role, tags } = await req.json()

    // Validate requesting_user_id
    if (!requesting_user_id || typeof requesting_user_id !== 'string') {
      return new Response(
        JSON.stringify({ error: 'Invalid requesting user ID' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    if (!uuidRegex.test(requesting_user_id)) {
      return new Response(
        JSON.stringify({ error: 'Invalid requesting user ID format' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate nfc_tag_id
    if (!nfc_tag_id || typeof nfc_tag_id !== 'string') {
      return new Response(
        JSON.stringify({ error: 'NFC Tag ID is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const sanitizedNfcId = nfc_tag_id.trim()
    if (sanitizedNfcId.length < 1 || sanitizedNfcId.length > 50 || !/^[a-zA-Z0-9]+$/.test(sanitizedNfcId)) {
      return new Response(
        JSON.stringify({ error: 'Invalid NFC tag ID format' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate name
    if (!name || typeof name !== 'string') {
      return new Response(
        JSON.stringify({ error: 'Name is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const sanitizedName = name.trim()
    if (sanitizedName.length < 1 || sanitizedName.length > 100) {
      return new Response(
        JSON.stringify({ error: 'Name must be between 1 and 100 characters' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate tags
    if (!Array.isArray(tags) || tags.length === 0) {
      return new Response(
        JSON.stringify({ error: 'At least one tag is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const validTags: UserTag[] = ['medetect_team', 'nurses', 'administrator']
    const sanitizedTags = tags.filter((tag: string) => validTags.includes(tag as UserTag)) as UserTag[]
    
    if (sanitizedTags.length === 0) {
      return new Response(
        JSON.stringify({ error: 'At least one valid tag is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate role (optional)
    const sanitizedRole = role ? String(role).trim().slice(0, 100) : null

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Verify requesting user has admin privileges
    const { data: requestingUser, error: authError } = await supabase
      .from('users')
      .select('tags')
      .eq('id', requesting_user_id)
      .maybeSingle()

    if (authError) {
      console.error('Auth error:', authError)
      return new Response(
        JSON.stringify({ error: 'Authorization failed' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    if (!requestingUser) {
      return new Response(
        JSON.stringify({ error: 'Requesting user not found' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const requestingUserTags = requestingUser.tags as UserTag[] | null
    const hasPermission = requestingUserTags?.includes('administrator') || 
                         requestingUserTags?.includes('medetect_team')

    if (!hasPermission) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - administrator or medetect_team privileges required' }),
        { status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Create the new user
    const { data: newUser, error: insertError } = await supabase
      .from('users')
      .insert({
        nfc_tag_id: sanitizedNfcId,
        name: sanitizedName,
        role: sanitizedRole,
        tags: sanitizedTags
      })
      .select('id, name, role, tags')
      .single()

    if (insertError) {
      console.error('Insert error:', insertError)
      
      // Check for duplicate NFC tag ID
      if (insertError.code === '23505') {
        return new Response(
          JSON.stringify({ error: 'A user with this NFC Tag ID already exists' }),
          { status: 409, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }
      
      return new Response(
        JSON.stringify({ error: 'Failed to create user' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    return new Response(
      JSON.stringify({ 
        success: true,
        user: newUser
      }),
      { status: 201, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (err) {
    console.error('Unexpected error:', err)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
