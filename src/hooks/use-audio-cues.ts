import { useCallback, useRef } from "react";

const AudioContext = window.AudioContext || (window as any).webkitAudioContext;

function playTone(frequency: number, duration: number, type: OscillatorType = "sine", volume = 0.3) {
  const ctx = new AudioContext();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();

  osc.type = type;
  osc.frequency.setValueAtTime(frequency, ctx.currentTime);
  gain.gain.setValueAtTime(volume, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + duration);

  setTimeout(() => ctx.close(), (duration + 0.1) * 1000);
}

/** Two rising tones – "ready to capture" */
function playReadySound() {
  playTone(660, 0.15, "sine", 0.35);
  setTimeout(() => playTone(880, 0.25, "sine", 0.35), 170);
}

/** Single low tone – "image captured, change tray" */
function playCapturedSound() {
  playTone(440, 0.12, "triangle", 0.3);
  setTimeout(() => playTone(520, 0.12, "triangle", 0.3), 130);
  setTimeout(() => playTone(660, 0.3, "triangle", 0.3), 260);
}

export function useAudioCues() {
  const countdownRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const signalReady = useCallback(() => {
    playReadySound();
  }, []);

  const signalCaptured = useCallback(() => {
    playCapturedSound();
  }, []);

  /** Play captured sound, then after `delaySec` seconds play ready sound */
  const signalCapturedThenReady = useCallback((delaySec = 5) => {
    playCapturedSound();
    if (countdownRef.current) clearTimeout(countdownRef.current);
    countdownRef.current = setTimeout(() => {
      playReadySound();
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
