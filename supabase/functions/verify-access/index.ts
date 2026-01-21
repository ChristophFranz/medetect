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
    const { user_id, required_tags } = await req.json()

    // Validate inputs
    if (!user_id || typeof user_id !== 'string') {
      return new Response(
        JSON.stringify({ authorized: false, error: 'Invalid user ID' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    if (!uuidRegex.test(user_id)) {
      return new Response(
        JSON.stringify({ authorized: false, error: 'Invalid user ID format' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    if (!Array.isArray(required_tags) || required_tags.length === 0) {
      return new Response(
        JSON.stringify({ authorized: false, error: 'Required tags must be a non-empty array' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Validate that required_tags contains only valid values
    const validTags: UserTag[] = ['medetect_team', 'nurses', 'administrator']
    const sanitizedTags = required_tags.filter((tag: string) => validTags.includes(tag as UserTag))
    
    if (sanitizedTags.length === 0) {
      return new Response(
        JSON.stringify({ authorized: false, error: 'No valid tags provided' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Fetch user's tags
    const { data: user, error } = await supabase
      .from('users')
      .select('id, name, tags')
      .eq('id', user_id)
      .maybeSingle()

    if (error) {
      console.error('Database error:', error)
      return new Response(
        JSON.stringify({ authorized: false, error: 'Database error' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    if (!user) {
      return new Response(
        JSON.stringify({ authorized: false, error: 'User not found' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Check if user has any of the required tags
    const userTags = user.tags as UserTag[] | null
    const authorized = userTags?.some(tag => sanitizedTags.includes(tag)) ?? false

    return new Response(
      JSON.stringify({ 
        authorized,
        user: {
          id: user.id,
          name: user.name,
          tags: userTags
        }
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (err) {
    console.error('Unexpected error:', err)
    return new Response(
      JSON.stringify({ authorized: false, error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
