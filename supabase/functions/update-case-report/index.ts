import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const { case_id, layer, report } = await req.json();

    if (!case_id || !layer || !report) {
      return new Response(
        JSON.stringify({ error: "Missing required fields: case_id, layer, report" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (layer !== "layer1" && layer !== "layer2") {
      return new Response(
        JSON.stringify({ error: "layer must be 'layer1' or 'layer2'" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const updateField = layer === "layer1" ? "layer1_report" : "layer2_report";

    const { error } = await supabase
      .from("inspection_cases")
      .update({ [updateField]: report })
      .eq("id", case_id);

    if (error) {
      console.error("Update error:", error);
      return new Response(
        JSON.stringify({ error: "Failed to update report" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({ success: true }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Error:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
