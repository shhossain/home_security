"use client";

import { apiClient } from "@/client";
import { Face } from "@/type/face";
import React, { createContext, useContext, useState, useEffect } from "react";

interface FaceContextType {
  knownFaces: Face[];
  unknownFaces: Face[];
  stats: {
    total_known: number;
    total_unknown: number;
    recent_attempts: number;
  };
  renameFace: (id: string, name: string) => Promise<void>;
  deleteFace: (id: string) => Promise<void>;
  refreshFaces: () => Promise<void>;
  uploadFace: (name: string, file: File) => Promise<void>;
}

const FaceContext = createContext<FaceContextType | undefined>(undefined);

export function FaceProvider({ children }: { children: React.ReactNode }) {
  const [knownFaces, setKnownFaces] = useState<Face[]>([]);
  const [unknownFaces, setUnknownFaces] = useState<Face[]>([]);
  const [stats, setStats] = useState({
    total_known: 0,
    total_unknown: 0,
    recent_attempts: 0,
  });

  const refreshFaces = async () => {
    const response = await apiClient("/faces", { cache: "no-cache" });
    const data = await response.json();
    console.log(data);
    setKnownFaces(data.faces.filter((f: Face) => !f.is_unknown));
    setUnknownFaces(data.faces.filter((f: Face) => f.is_unknown));
    setStats(data.stats);
  };

  const renameFace = async (id: string, name: string) => {
    const response = await apiClient(`/faces/${id}/rename`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (response.ok) {
      await refreshFaces();
    }
  };

  const deleteFace = async (id: string) => {
    const response = await apiClient(`/faces/${id}/delete`, {
      method: "POST",
    });
    if (response.ok) {
      await refreshFaces();
    }
  };

  const uploadFace = async (name: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);

    await fetch(`${API_URL}/faces/upload`, {
      method: 'POST',
      body: formData,
    });

    // Refresh faces after upload
    fetchFaces();
  };

  useEffect(() => {
    refreshFaces();
    const interval = setInterval(refreshFaces, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <FaceContext.Provider
      value={{
        knownFaces,
        unknownFaces,
        stats,
        renameFace,
        deleteFace,
        refreshFaces,
        uploadFace,
      }}
    >
      {children}
    </FaceContext.Provider>
  );
}

export const useFaces = () => {
  const context = useContext(FaceContext);
  if (!context) {
    throw new Error("useFaces must be used within a FaceProvider");
  }
  return context;
};
