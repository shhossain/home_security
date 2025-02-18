"use client";

import { useFaces } from "@/contexts/FaceContext";
import { Card, CardDescription, CardHeader } from "./ui/card";
import FaceCard from "./FaceCard";
import { VideoFeed } from "./VideoFeed";
import { AddFaceDialog } from "./AddFaceDialog";
import { useState } from "react";
import { Button } from "./ui/button";
import { Eye, EyeOff } from "lucide-react";

export function HomePage() {
  const { knownFaces, unknownFaces, stats, renameFace, deleteFace, uploadFace } = useFaces();
  const [showVideo, setShowVideo] = useState(false);

  return (
    <div className="container mx-auto py-8 space-y-8 px-4">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2">Face Recognition System</h1>
          <p className="text-muted-foreground">Monitor and manage detected faces</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowVideo(!showVideo)}
            className="flex items-center gap-2"
          >
            {showVideo ? (
              <>
                <EyeOff className="h-4 w-4" /> Hide Camera
              </>
            ) : (
              <>
                <Eye className="h-4 w-4" /> Show Camera
              </>
            )}
          </Button>
          <AddFaceDialog onAddFace={uploadFace} />
        </div>
      </div>

      {showVideo && (
        <Card className="overflow-hidden">
          <VideoFeed />
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6">
          <CardHeader className="pb-2">Known Faces</CardHeader>
          <CardDescription className="text-3xl font-semibold">{stats.total_known}</CardDescription>
        </Card>
        <Card className="p-6">
          <CardHeader className="pb-2">Unknown Faces</CardHeader>
          <CardDescription className="text-3xl font-semibold">{stats.total_unknown}</CardDescription>
        </Card>
        <Card className="p-6">
          <CardHeader className="pb-2">Recent Attempts</CardHeader>
          <CardDescription className="text-3xl font-semibold">{stats.recent_attempts}</CardDescription>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-8">
        <section>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Known Faces</h2>
            <span className="text-sm text-muted-foreground">
              Total: {knownFaces.length}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {knownFaces.map((face) => (
              <FaceCard key={face.id} face={face} onRename={renameFace} onDelete={deleteFace} />
            ))}
            {knownFaces.length === 0 && (
              <p className="text-muted-foreground col-span-full text-center py-8">
                No known faces found
              </p>
            )}
          </div>
        </section>

        <section>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Unknown Faces</h2>
            <span className="text-sm text-muted-foreground">
              Total: {unknownFaces.length}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {unknownFaces.map((face) => (
              <FaceCard key={face.id} face={face} onRename={renameFace} onDelete={deleteFace} />
            ))}
            {unknownFaces.length === 0 && (
              <p className="text-muted-foreground col-span-full text-center py-8">
                No unknown faces detected
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
