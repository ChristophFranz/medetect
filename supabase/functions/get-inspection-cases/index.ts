import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const { filter_type, filter_value, search_query } = await req.json();

    let query = supabase
      .from('inspection_cases')
      .select('*')
      .order('created_at', { ascending: false });

    // Apply search query if provided
    if (search_query && search_query.trim()) {
      const searchTerm = search_query.trim().toLowerCase();
      query = query.or(`patient_name.ilike.%${searchTerm}%,user_name.ilike.%${searchTerm}%,folder_path.ilike.%${searchTerm}%`);
    }

    // Apply filters based on filter_type
    if (filter_type === 'user' && filter_value) {
      query = query.eq('user_id', filter_value);
    } else if (filter_type === 'date' && filter_value) {
      // Filter by specific date
      const startDate = new Date(filter_value);
      startDate.setHours(0, 0, 0, 0);
      const endDate = new Date(filter_value);
      endDate.setHours(23, 59, 59, 999);
      query = query.gte('created_at', startDate.toISOString()).lte('created_at', endDate.toISOString());
    }

    const { data: cases, error } = await query;

    if (error) {
      console.error('Error fetching cases:', error);
      return new Response(
        JSON.stringify({ error: 'Failed to fetch cases' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({ success: true, cases }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
