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
  "hook sinskey tip": "hook-sinskey",
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

    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const casePrefix = `cases/${case_id}/${layer}`;

    // 1. Save the annotated toolbox image to case-images bucket
    let annotatedImagePath: string | null = null;
    if (report.annotated_image) {
      try {
        const { bytes, contentType } = base64ToBytes(report.annotated_image);
        const ext = contentType.includes("png") ? "png" : "jpg";
        const filePath = `${casePrefix}/annotated_${timestamp}.${ext}`;

        const { error: uploadError } = await supabase.storage
          .from("case-images")
          .upload(filePath, bytes, { contentType, upsert: true });

        if (uploadError) {
          console.error("Failed to upload annotated image:", uploadError);
        } else {
          annotatedImagePath = filePath;
        }
      } catch (imgErr) {
        console.error("Error processing annotated image:", imgErr);
      }
    }

    // 2. Save individual tool crop images to both case-images (for case viewing) and tool-images (for classification)
    const toolImageResults: string[] = [];
    const toolsWithPaths = [];

    for (const tool of (report.tools || [])) {
      let toolImagePath: string | null = null;

      if (tool.image && tool.name) {
        try {
          const { bytes, contentType } = base64ToBytes(tool.image);
          const ext = contentType.includes("png") ? "png" : "jpg";
          const safeName = tool.name.toLowerCase().replace(/\s+/g, "-");

          // Save to case-images for case-level viewing
          const caseFilePath = `${casePrefix}/tool_${safeName}_${timestamp}.${ext}`;
          const { error: caseUploadErr } = await supabase.storage
            .from("case-images")
            .upload(caseFilePath, bytes, { contentType, upsert: true });

          if (caseUploadErr) {
            console.error(`Failed to upload case tool image for ${tool.name}:`, caseUploadErr);
          } else {
            toolImagePath = caseFilePath;
          }

          // Also save to tool-images for classification database
          const folderName = toolFolderMap[tool.name.toLowerCase()];
          if (folderName) {
            const classFilePath = `${folderName}/case-${case_id.slice(0, 8)}_${layer}_${timestamp}.${ext}`;
            const { error: classUploadErr } = await supabase.storage
              .from("tool-images")
              .upload(classFilePath, bytes, { contentType, upsert: true });

            if (classUploadErr) {
              console.error(`Failed to upload classification image for ${tool.name}:`, classUploadErr);
            } else {
              toolImageResults.push(classFilePath);
            }
          }
        } catch (imgErr) {
          console.error(`Error processing image for ${tool.name}:`, imgErr);
        }
      }

      // Store the path (not base64) in the report
      toolsWithPaths.push({
        name: tool.name,
        count: tool.count,
        status: tool.status,
        image_path: toolImagePath,
      });
    }

    // 3. Build lightweight report with storage paths instead of base64
    const reportForDb = {
      overall: report.overall,
      annotated_image_path: annotatedImagePath,
      tools: toolsWithPaths,
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

    return new Response(
      JSON.stringify({ success: true, tool_images_saved: toolImageResults, annotated_image_saved: !!annotatedImagePath }),
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
