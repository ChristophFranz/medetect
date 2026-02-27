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
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const {
      case_id,
      layer,
      tool_name,
      new_status,
      primary_user_id,
      primary_user_name,
      second_user_id,
      second_user_name,
    } = await req.json();

    // Validate inputs
    if (!case_id || !layer || !tool_name || !new_status || !primary_user_id || !second_user_id) {
      return new Response(
        JSON.stringify({ error: "Missing required fields" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (layer !== "layer1" && layer !== "layer2") {
      return new Response(
        JSON.stringify({ error: "layer must be 'layer1' or 'layer2'" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    if (primary_user_id === second_user_id) {
      return new Response(
        JSON.stringify({ error: "Second user must be different from primary user" }),
        { status: 403, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Verify second user exists
    const { data: secondUser, error: userError } = await supabase
      .from("users")
      .select("id, name")
      .eq("id", second_user_id)
      .maybeSingle();

    if (userError || !secondUser) {
      return new Response(
        JSON.stringify({ error: "Second user not found" }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Fetch the current case
    const reportField = layer === "layer1" ? "layer1_report" : "layer2_report";
    const { data: caseData, error: caseError } = await supabase
      .from("inspection_cases")
      .select(reportField)
      .eq("id", case_id)
      .maybeSingle();

    if (caseError || !caseData) {
      return new Response(
        JSON.stringify({ error: "Case not found" }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Update the tool status in the report
    const report = (caseData as any)[reportField] as any;
    if (!report || !report.tools) {
      return new Response(
        JSON.stringify({ error: "Report not found for this layer" }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const toolIndex = report.tools.findIndex(
      (t: any) => t.name.toLowerCase() === tool_name.toLowerCase()
    );

    if (toolIndex === -1) {
      return new Response(
        JSON.stringify({ error: "Tool not found in report" }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Store old status for audit
    const oldStatus = report.tools[toolIndex].status;

    // Update the tool status and add override metadata
    report.tools[toolIndex].status = new_status;
    report.tools[toolIndex].status_override = {
      original_status: oldStatus,
      new_status,
      primary_user: { id: primary_user_id, name: primary_user_name },
      second_user: { id: second_user_id, name: second_user_name },
      overridden_at: new Date().toISOString(),
    };

    // Recalculate overall status
    const hasDefective = report.tools.some(
      (t: any) => t.status.toLowerCase().includes("defective") && !t.status.toLowerCase().includes("non")
    );
    report.overall = hasDefective
      ? "Issue detected – some tools are defective"
      : "All present and non-defective";

    // Save updated report
    const { error: updateError } = await supabase
      .from("inspection_cases")
      .update({ [reportField]: report })
      .eq("id", case_id);

    if (updateError) {
      console.error("Update error:", updateError);
      return new Response(
        JSON.stringify({ error: "Failed to save status override" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        tool_name,
        old_status: oldStatus,
        new_status,
        confirmed_by: second_user_name,
      }),
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
