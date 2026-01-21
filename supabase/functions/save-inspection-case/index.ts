import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Random patient names for demo purposes
const patientNames = [
  "John Smith",
  "Maria Garcia",
  "David Chen",
  "Sarah Johnson",
  "Michael Brown",
  "Emily Davis",
  "James Wilson",
  "Lisa Anderson",
  "Robert Taylor",
  "Jennifer Martinez",
];

function getRandomPatientName(): string {
  return patientNames[Math.floor(Math.random() * patientNames.length)];
}

function base64ToBlob(base64: string): { blob: Uint8Array; contentType: string } {
  const matches = base64.match(/^data:(.+);base64,(.+)$/);
  if (!matches) {
    throw new Error("Invalid base64 string");
  }
  const contentType = matches[1];
  const base64Data = matches[2];
  const binaryString = atob(base64Data);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return { blob: bytes, contentType };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const { user_id, user_name, layer1_image, layer2_image } = await req.json();

    if (!user_id || !user_name || !layer1_image || !layer2_image) {
      return new Response(
        JSON.stringify({ error: "Missing required fields" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Generate patient name and timestamp
    const patientName = getRandomPatientName();
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, "-");
    const displayDate = now.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
    const displayTime = now.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
    });

    // Get the next case number
    const { data: lastCase } = await supabase
      .from("inspection_cases")
      .select("case_number")
      .order("case_number", { ascending: false })
      .limit(1)
      .single();

    const caseNumber = (lastCase?.case_number || 0) + 1;
    const folderPath = `Case ${String(caseNumber).padStart(2, "0")}: ${patientName} - ${user_name} - ${displayTime} ${displayDate}`;
    const sanitizedFolderPath = folderPath.replace(/[/\\?%*:|"<>]/g, "-");

    // Upload layer 1 image
    const layer1Data = base64ToBlob(layer1_image);
    const layer1Path = `${sanitizedFolderPath}/layer1.jpg`;
    const { error: layer1Error } = await supabase.storage
      .from("case-images")
      .upload(layer1Path, layer1Data.blob, {
        contentType: layer1Data.contentType,
        upsert: true,
      });

    if (layer1Error) {
      console.error("Layer 1 upload error:", layer1Error);
      return new Response(
        JSON.stringify({ error: "Failed to upload layer 1 image" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Upload layer 2 image
    const layer2Data = base64ToBlob(layer2_image);
    const layer2Path = `${sanitizedFolderPath}/layer2.jpg`;
    const { error: layer2Error } = await supabase.storage
      .from("case-images")
      .upload(layer2Path, layer2Data.blob, {
        contentType: layer2Data.contentType,
        upsert: true,
      });

    if (layer2Error) {
      console.error("Layer 2 upload error:", layer2Error);
      return new Response(
        JSON.stringify({ error: "Failed to upload layer 2 image" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Insert case record
    const { data: caseData, error: caseError } = await supabase
      .from("inspection_cases")
      .insert({
        case_number: caseNumber,
        patient_name: patientName,
        user_id,
        user_name,
        folder_path: sanitizedFolderPath,
        layer1_image_path: layer1Path,
        layer2_image_path: layer2Path,
      })
      .select()
      .single();

    if (caseError) {
      console.error("Case insert error:", caseError);
      return new Response(
        JSON.stringify({ error: "Failed to save case record" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        case: {
          id: caseData.id,
          case_number: caseNumber,
          patient_name: patientName,
          folder_path: sanitizedFolderPath,
        },
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
