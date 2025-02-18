"use client";

import { useEffect, useRef } from 'react';
import { Card } from './ui/card';

export function VideoFeed() {
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/video');
    
    ws.onmessage = (event) => {
      if (imgRef.current) {
        imgRef.current.src = URL.createObjectURL(event.data);
      }
    };

    ws.onclose = () => {
      console.log('Connection closed');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <Card className="p-4">
      <img
        ref={imgRef}
        alt="Live Feed"
        className="w-full h-[480px] object-contain rounded-lg"
      />
    </Card>
  );
}
