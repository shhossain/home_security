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

    ws.onopen = () => {
      setIsConnecting(false);
      setError(null);
    };

    ws.onmessage = (event) => {
      if (imageRef.current) {
        // Clean up previous blob URL
        if (currentBlobUrl.current) {
          URL.revokeObjectURL(currentBlobUrl.current);
        }

        const blob = new Blob([event.data], { type: "image/jpeg" });
        const url = URL.createObjectURL(blob);
        currentBlobUrl.current = url;

        // Use requestAnimationFrame for smoother updates
        requestAnimationFrame(() => {
          if (imageRef.current) {
            imageRef.current.src = url;
          }
        });
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
    <div className="relative">
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
        className="w-full max-h-[600px] object-contain bg-slate-950"
        alt="Video Feed"
        style={{
          imageRendering: "auto",
          maxWidth: "1280px",
          margin: "0 auto",
        }}
      />
    </div>
  );
}
