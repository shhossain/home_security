import { useState } from "react";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { format } from "date-fns";
import { Face } from "@/type/face";

interface FaceCardProps {
  face: Face;
  onRename: (id: string, name: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export default function FaceCard({ face, onRename, onDelete }: FaceCardProps) {
  const [newName, setNewName] = useState(face.name);

  return (
    <Card className={`p-4 ${face.liveness < 0.5 ? "border-red-500" : ""}`}>
      <div className="relative">
        <img src={`/api/faces/image/${face.id}`} alt={face.name} className="w-full h-48 object-cover rounded-md" />
        <div 
          className={`absolute top-2 right-2 w-3 h-3 rounded-full ${
            face.active ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
      </div>
      <div className="mt-4 space-y-2">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            await onRename(face.id, newName);
          }}
          className="flex gap-2"
        >
          <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder={face.is_unknown ? "Give a name" : ""} />
          <Button type="submit">{face.is_unknown ? "Save" : "Rename"}</Button>
        </form>
        <p className="text-sm text-gray-500">Last seen: {format(new Date(face.last_seen), "yyyy-MM-dd HH:mm")}</p>
        {face.is_unknown && <p className="text-sm text-gray-500">First seen: {format(new Date(face.createdAt!), "yyyy-MM-dd HH:mm")}</p>}
        <p className="text-sm text-gray-500">Liveness: {(face.liveness * 100).toFixed(0) + "%"} </p>
        <Button
          variant="destructive"
          onClick={() => {
            if (confirm("Are you sure you want to delete this face?")) {
              onDelete(face.id);
            }
          }}
        >
          Delete
        </Button>
      </div>
    </Card>
  );
}
