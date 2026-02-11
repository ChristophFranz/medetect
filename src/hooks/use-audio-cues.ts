import { useCallback, useRef } from "react";

function speak(text: string) {
  if (!("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  window.speechSynthesis.speak(utterance);
}

export type PositionContext = "layer1" | "layer2" | "recapture";

export function useAudioCues() {
  const countdownRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** Speak positioning prompt, then "Ready to capture image" after delaySec */
  const signalPosition = useCallback((context: PositionContext, delaySec = 5) => {
    if (countdownRef.current) clearTimeout(countdownRef.current);

    const msg =
      context === "layer1" ? "Position the top layer" :
      context === "layer2" ? "Position the 2nd layer" :
      "Position the layer for recapture";

    speak(msg);
    countdownRef.current = setTimeout(() => {
      speak("Ready to capture image");
      countdownRef.current = null;
    }, delaySec * 1000);
  }, []);

  const signalCaptured = useCallback(() => {
    speak("Image captured");
  }, []);

  const signalInspectionComplete = useCallback(() => {
    speak("Inspection successful, analysing tools");
  }, []);

  const cancelPending = useCallback(() => {
    if (countdownRef.current) {
      clearTimeout(countdownRef.current);
      countdownRef.current = null;
    }
  }, []);

  return { signalPosition, signalCaptured, signalInspectionComplete, cancelPending };
}
