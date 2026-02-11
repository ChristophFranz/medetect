import { useEffect, useRef, useState, useCallback } from "react";

interface UseVoiceCommandOptions {
  commands: Record<string, () => void>;
  enabled?: boolean;
  continuous?: boolean;
}

// Type definitions for Web Speech API
type SpeechRecognitionResult = {
  isFinal: boolean;
  [index: number]: { transcript: string };
};

type SpeechRecognitionType = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onstart: (() => void) | null;
  onresult: ((event: { results: { length: number; [index: number]: SpeechRecognitionResult } }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
};

export function useVoiceCommand({ commands, enabled = true, continuous = true }: UseVoiceCommandOptions) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [lastCommand, setLastCommand] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string>("");
  const [isCommandMatch, setIsCommandMatch] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionType | null>(null);
  const transcriptTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognitionConstructor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognitionConstructor);
  }, []);

  const startListening = useCallback(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognitionConstructor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognitionConstructor || !enabled) return;

    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    const recognition = new SpeechRecognitionConstructor() as SpeechRecognitionType;
    recognition.continuous = continuous;
    recognition.interimResults = true; // Enable interim results for real-time display
    recognition.lang = "en-US";

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const lastResult = event.results[event.results.length - 1];
      const transcriptText = lastResult[0].transcript.toLowerCase().trim();
      
      // Update transcript display
      setTranscript(transcriptText);
      
      // Clear previous timeout
      if (transcriptTimeoutRef.current) {
        clearTimeout(transcriptTimeoutRef.current);
      }
      
      if (lastResult.isFinal) {
        console.log("Voice command heard:", transcriptText);
        
        // Check if any command matches
        let matched = false;
        for (const [command, handler] of Object.entries(commands)) {
          if (transcriptText.includes(command.toLowerCase())) {
            setLastCommand(command);
            setIsCommandMatch(true);
            matched = true;
            handler();
            break;
          }
        }
        
        if (!matched) {
          setIsCommandMatch(false);
        }
        
        // Clear transcript after 2 seconds
        transcriptTimeoutRef.current = setTimeout(() => {
          setTranscript("");
          setIsCommandMatch(false);
        }, 2000);
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      if (event.error !== "no-speech" && event.error !== "aborted") {
        setIsListening(false);
      }
    };

    recognition.onend = () => {
      // Only mark as not listening if we're NOT going to restart
      if (continuous && enabled && recognitionRef.current === recognition) {
        try {
          recognition.start();
        } catch (e) {
          console.log("Could not restart recognition");
          setIsListening(false);
        }
      } else {
        setIsListening(false);
      }
    };

    recognitionRef.current = recognition;
    
    try {
      recognition.start();
    } catch (e) {
      console.error("Failed to start speech recognition:", e);
    }
  }, [commands, enabled, continuous]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  useEffect(() => {
    if (enabled && isSupported) {
      startListening();
    } else {
      stopListening();
    }

    return () => {
      stopListening();
    };
  }, [enabled, isSupported, startListening, stopListening]);

  return {
    isListening,
    isSupported,
    lastCommand,
    transcript,
    isCommandMatch,
    startListening,
    stopListening,
  };
}
