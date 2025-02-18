"use client";

import { useFaces } from "@/contexts/FaceContext";
import { Card, CardDescription, CardHeader } from "./ui/card";
import FaceCard from "./FaceCard";
import { VideoFeed } from "./VideoFeed";

export function HomePage() {
  const { knownFaces, unknownFaces, stats, renameFace, deleteFace } = useFaces();

  return (
    <div className="container mx-auto py-8 space-y-8">
      <VideoFeed />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <CardHeader>Known Faces</CardHeader>
          <CardDescription className="text-2xl">{stats.total_known}</CardDescription>
        </Card>
        <Card className="p-4">
          <CardHeader>Unknown Faces</CardHeader>
          <CardDescription className="text-2xl">{stats.total_unknown}</CardDescription>
        </Card>
        <Card className="p-4">
          <CardHeader>Recent Attempts</CardHeader>
          <CardDescription className="text-2xl">{stats.recent_attempts}</CardDescription>
        </Card>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4">Known Faces</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {knownFaces.map((face) => (
            <FaceCard key={face.id} face={face} onRename={renameFace} onDelete={deleteFace} />
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4">Unknown Faces</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {unknownFaces.map((face) => (
            <FaceCard key={face.id} face={face} onRename={renameFace} onDelete={deleteFace} />
          ))}
        </div>
      </div>
    </div>
  );
}
