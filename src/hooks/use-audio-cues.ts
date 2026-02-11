import { useCallback, useRef } from "react";

function speak(text: string, onEnd?: () => void) {
  if (!("speechSynthesis" in window)) {
    onEnd?.();
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  if (onEnd) {
    utterance.onend = () => onEnd();
  }
  window.speechSynthesis.speak(utterance);
}

export type PositionContext = "layer1" | "layer2" | "recapture";

interface UseAudioCuesOptions {
  onReadyToCapture?: () => void;
}

export function useAudioCues(options?: UseAudioCuesOptions) {
  const countdownRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onReadyRef = useRef(options?.onReadyToCapture);
  onReadyRef.current = options?.onReadyToCapture;

  /** Speak positioning prompt, then "Ready to capture image" after delaySec */
  const signalPosition = useCallback((context: PositionContext, delaySec = 5) => {
    if (countdownRef.current) clearTimeout(countdownRef.current);

    const msg =
      context === "layer1" ? "Position the top layer" :
      context === "layer2" ? "Position the 2nd layer" :
      "Position the layer for recapture";

    speak(msg);
    countdownRef.current = setTimeout(() => {
      speak("Ready to capture image", () => {
        // After TTS finishes, signal that mic should be active
        onReadyRef.current?.();
      });
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
