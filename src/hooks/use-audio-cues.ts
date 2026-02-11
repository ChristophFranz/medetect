import { useCallback, useRef } from "react";

function speak(text: string) {
  if (!("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  window.speechSynthesis.speak(utterance);
}

export function useAudioCues() {
  const countdownRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const signalReady = useCallback(() => {
    speak("Ready to capture image");
  }, []);

  const signalCaptured = useCallback(() => {
    speak("Image captured");
  }, []);

  /** Speak "Image captured", then after `delaySec` seconds speak "Ready to capture image" */
  const signalCapturedThenReady = useCallback((delaySec = 5) => {
    speak("Image captured");
    if (countdownRef.current) clearTimeout(countdownRef.current);
    countdownRef.current = setTimeout(() => {
      speak("Ready to capture image");
      countdownRef.current = null;
    }, delaySec * 1000);
  }, []);

  const cancelPending = useCallback(() => {
    if (countdownRef.current) {
      clearTimeout(countdownRef.current);
      countdownRef.current = null;
    }
  }, []);

  return { signalReady, signalCaptured, signalCapturedThenReady, cancelPending };
}
