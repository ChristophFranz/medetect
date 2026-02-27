import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const toolFolderMap: Record<string, string> = {
  "chop phaco": "chop-phaco",
  "forceps macpherson": "forceps-macpherson",
  "forceps utrata": "forceps-utrata",
  "hook sinskey": "hook-sinskey",
};

function base64ToBytes(base64: string): { bytes: Uint8Array; contentType: string } {
  const matches = base64.match(/^data:(.+);base64,(.+)$/);
  if (!matches) throw new Error("Invalid base64 string");
  const contentType = matches[1];
  const binaryString = atob(matches[2]);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return { bytes, contentType };
}

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

    // Strip base64 images from the report before saving to DB (keep it lightweight)
    const reportForDb = {
      ...report,
      annotated_image: undefined,
      tools: (report.tools || []).map((t: any) => ({
        name: t.name,
        count: t.count,
        status: t.status,
        // Don't store base64 in jsonb
      })),
    };

    const updateField = layer === "layer1" ? "layer1_report" : "layer2_report";

    const { error } = await supabase
      .from("inspection_cases")
      .update({ [updateField]: reportForDb })
      .eq("id", case_id);

    if (error) {
      console.error("Update error:", error);
      return new Response(
        JSON.stringify({ error: "Failed to update report" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Save individual tool images to tool-images bucket
    const toolImageResults: string[] = [];
    const tools = report.tools || [];
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");

    for (const tool of tools) {
      if (!tool.image || !tool.name) continue;

      const folderName = toolFolderMap[tool.name.toLowerCase()];
      if (!folderName) {
        console.warn(`Unknown tool name: ${tool.name}, skipping image save`);
        continue;
      }

      try {
        const { bytes, contentType } = base64ToBytes(tool.image);
        const ext = contentType.includes("png") ? "png" : "jpg";
        const fileName = `case-${case_id.slice(0, 8)}_${layer}_${timestamp}.${ext}`;
        const filePath = `${folderName}/${fileName}`;

        const { error: uploadError } = await supabase.storage
          .from("tool-images")
          .upload(filePath, bytes, {
            contentType,
            upsert: true,
          });

        if (uploadError) {
          console.error(`Failed to upload tool image for ${tool.name}:`, uploadError);
        } else {
          toolImageResults.push(filePath);
        }
      } catch (imgErr) {
        console.error(`Error processing image for ${tool.name}:`, imgErr);
      }
    }

    return new Response(
      JSON.stringify({ success: true, tool_images_saved: toolImageResults }),
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
