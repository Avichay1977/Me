'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, StopCircle, Camera, Loader2, MessageSquareText, Code, Volume2, VolumeX } from 'lucide-react';

interface Message {
  text: string;
  sender: 'user' | 'ai';
  isCode?: boolean;
}

const CubaseCopilot = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null);

  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserNodeRef = useRef<AnalyserNode | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioPlayerRef = useRef<HTMLAudioElement>(null);

  const [hasMicrophonePermission, setHasMicrophonePermission] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const stopAllStreams = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current.onend = null;
    }
    audioStream?.getTracks().forEach(track => track.stop());
    videoStream?.getTracks().forEach(track => track.stop());
    audioContextRef.current?.close().catch(console.error);

    setAudioStream(null);
    setVideoStream(null);
    setHasMicrophonePermission(false);
    setIsCapturing(false);
    setIsLoading(false);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, [audioStream, videoStream]);


  const sendToAI = async (prompt: string) => {
    setIsLoading(true);
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    let imageBase64: string | null = null;
    if (videoRef.current && videoStream && videoRef.current.videoWidth > 0) {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        imageBase64 = canvas.toDataURL('image/jpeg', 0.5);
      }
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, imageBase64 }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "An unknown error occurred");
      }

      const data = await response.json();
      setMessages(prev => [...prev, { text: data.text, sender: 'ai', isCode: data.isCode }]);

      if (data.audioBuffer) {
        const audioBlob = new Blob([new Uint8Array(data.audioBuffer.data)], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        if (audioPlayerRef.current) {
          audioPlayerRef.current.src = audioUrl;
          audioPlayerRef.current.play().catch(e => console.error("Error playing audio:", e));
        }
      } else {
         if (isCapturing) {
            recognitionRef.current?.start();
         }
      }
    } catch (error: any) {
      console.error("Failed to send prompt to AI:", error);
      toast.error(error.message || "Failed to get a response from the AI.");
    } finally {
      setIsLoading(false);
    }
  };

  const startRecognition = useCallback(() => {
    if (!('webkitSpeechRecognition' in window)) {
      toast.error("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new (window as any).webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'he-IL';
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setMessages(prev => [...prev, { text: transcript, sender: 'user' }]);
      sendToAI(transcript);
    };

    recognition.onerror = (event: any) => {
      if (event.error !== 'no-speech') {
        console.error('Speech recognition error:', event.error);
        toast.error(`Speech recognition error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      if (isCapturing && !isLoading && !isSpeaking) {
        recognition.start();
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isCapturing, isLoading, isSpeaking]);

  const startAssistant = async () => {
    setIsCapturing(true);
    try {
      const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setAudioStream(micStream);
      setHasMicrophonePermission(true);

      try {
        const displayStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        setVideoStream(displayStream);
        if (videoRef.current) {
          videoRef.current.srcObject = displayStream;
        }
      } catch (err: any) {
        if (err.name === 'NotAllowedError') {
          toast.error("Screen sharing is not available. Continuing with microphone only.", { duration: 5000 });
        } else {
          toast.error(`Screen share error: ${err.message}`);
        }
      }

      const context = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = context.createMediaStreamSource(micStream);
      const analyser = context.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      audioContextRef.current = context;
      analyserNodeRef.current = analyser;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      const canvas = canvasRef.current;
      const canvasCtx = canvas?.getContext('2d');

      if (canvasCtx && canvas) {
        const draw = () => {
          if (!analyserNodeRef.current || !canvasCtx || !canvas || !isCapturing) {
             if (canvasCtx) canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
             return;
          }
          requestAnimationFrame(draw);
          analyserNodeRef.current.getByteFrequencyData(dataArray);
          canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
          const barWidth = (canvas.width / bufferLength) * 2.5;
          let x = 0;
          for (let i = 0; i < bufferLength; i++) {
            const barHeight = dataArray[i];
            const blueValue = barHeight / 2;
            canvasCtx.fillStyle = `rgb(50, 50, ${150 + blueValue})`;
            canvasCtx.fillRect(x, canvas.height - barHeight / 2, barWidth, barHeight / 2);
            x += barWidth + 1;
          }
        };
        draw();
      }
      startRecognition();
    } catch (err: any) {
      toast.error(`Error starting assistant: ${err.message}.`);
      stopAllStreams();
    }
  };

  const handleAudioPlayerEvents = () => {
    const player = audioPlayerRef.current;
    if (player) {
      player.onplay = () => setIsSpeaking(true);
      player.onended = () => {
        setIsSpeaking(false);
        if (isCapturing && !isLoading) {
          recognitionRef.current?.start();
        }
      };
      player.onerror = () => {
        setIsSpeaking(false);
        toast.error("Failed to play audio response.");
      }
    }
  };

  useEffect(() => {
    handleAudioPlayerEvents();
    return () => {
      stopAllStreams();
    };
  }, [stopAllStreams]);

  return (
    <div className="flex flex-col min-h-screen bg-dark-bg text-gray-200 p-4 items-center font-inter">
      <h1 className="text-4xl font-bold mb-8 text-center">Pro Audio Assistant</h1>

      <div className="flex flex-col md:flex-row w-full max-w-6xl gap-8">
        <div className="flex-1 flex flex-col items-center">
          <div className="w-full bg-dark-card rounded-lg p-6 flex flex-col h-[70vh] shadow-xl border border-dark-border">
            <div className="flex-1 overflow-y-auto mb-4 p-2 custom-scrollbar">
              <AnimatePresence>
                {messages.map((message, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`flex my-3 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`chat-bubble ${message.sender}`}>
                      {message.isCode ? (
                        <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-800 p-3 rounded-md">
                          <div className="flex items-center text-gray-400 text-xs mb-2"><Code size={14} className="mr-2"/> JavaScript</div>
                          <code>{message.text}</code>
                        </pre>
                      ) : (
                        <div className="flex items-center">
                          {message.text}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>

            <div className="flex justify-center items-center mt-4 space-x-4">
              <button
                onClick={isCapturing ? stopAllStreams : startAssistant}
                className={`px-6 py-3 rounded-full text-lg font-semibold transition-all duration-300 flex items-center justify-center gap-2 ${
                  isCapturing
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-green-600 hover:bg-green-700'
                } text-white`}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    טוען...
                  </>
                ) : isCapturing ? (
                  <>
                    <StopCircle size={20} />
                    עצור
                  </>
                ) : (
                  <>
                    <Mic size={20} />
                    התחל
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center">
          <div className="w-full bg-dark-card rounded-lg p-4 mb-8 h-[300px] shadow-xl border border-dark-border flex flex-col">
            <h2 className="text-center text-lg mb-2 text-white">מנתח אודיו</h2>
            <div className="h-full w-full flex items-center justify-center bg-black rounded-md">
              <canvas ref={canvasRef} className="w-full h-full"></canvas>
            </div>
          </div>

          <div className="w-full bg-dark-card rounded-lg p-4 h-[300px] shadow-xl border border-dark-border flex flex-col">
            <h2 className="text-center text-lg mb-2 text-white">שיתוף מסך</h2>
            <div className="flex-1 flex items-center justify-center w-full max-h-[200px] overflow-hidden rounded-md bg-black">
              {videoStream ? (
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-contain" />
              ) : (
                <div className="text-gray-500 text-center p-2">
                  <p>שיתוף מסך יופיע כאן</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <audio ref={audioPlayerRef} onPlay={() => setIsSpeaking(true)} onEnded={() => setIsSpeaking(false)} onError={() => setIsSpeaking(false)} />
    </div>
  );
};

export default CubaseCopilot;
