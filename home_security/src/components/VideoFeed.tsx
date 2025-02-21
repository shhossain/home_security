"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "./ui/button";
import { Loader2 } from "lucide-react";

export function VideoFeed() {
  const [isConnecting, setIsConnecting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const currentBlobUrl = useRef<string | null>(null);

  const connect = () => {
    setIsConnecting(true);
    setError(null);

    const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/video`);
    wsRef.current = ws;

    // Set binary type to arraybuffer for better performance
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      setIsConnecting(false);
      setError(null);
    };

    ws.onmessage = async (event) => {
      if (!imageRef.current) return;

      try {
        // Skip size message
        if (event.data.byteLength === 4) return;

        const blob = new Blob([event.data], { type: "image/jpeg" });
        if (blob.size < 100) return;

        // Create object URL directly without validation
        const url = URL.createObjectURL(blob);

        // Cleanup previous URL
        if (currentBlobUrl.current) {
          URL.revokeObjectURL(currentBlobUrl.current);
        }

        currentBlobUrl.current = url;
        imageRef.current.src = url;
      } catch (error) {
        console.error("Error processing frame:", error);
      }
    };

    ws.onerror = () => {
      setError("Connection error");
      reconnect();
    };

    ws.onclose = () => {
      setError("Connection closed");
      reconnect();
    };
  };

  const reconnect = () => {
    wsRef.current?.close();
    clearTimeout(reconnectTimeoutRef.current);
    reconnectTimeoutRef.current = setTimeout(connect, 2000);
  };

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      clearTimeout(reconnectTimeoutRef.current);
      if (currentBlobUrl.current) {
        URL.revokeObjectURL(currentBlobUrl.current);
      }
    };
  }, []);

  return (
    <div className="relative w-full aspect-video max-w-[1280px] max-h-[600px] mx-auto bg-slate-950">
      {isConnecting && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/50">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Connecting to camera...</span>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/50">
          <div className="flex flex-col items-center gap-4">
            <p className="text-destructive">{error}</p>
            <Button onClick={connect} variant="outline" size="sm">
              Try Again
            </Button>
          </div>
        </div>
      )}

      <img
        ref={imageRef}
        className="w-full h-full object-contain"
        alt="Video Feed"
        style={{
          // imageRendering: "optimizeSpeed",
          willChange: "transform",
        }}
      />
    </div>
  );
}
