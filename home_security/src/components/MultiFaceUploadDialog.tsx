import { useState } from "react";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Loader2, Upload } from "lucide-react";
import { apiClient } from "@/client";
import { VisuallyHidden } from "./ui/visually-hidden";

interface DetectedFace {
  id: number;
  bbox: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
  image_data: string;
}

interface MultiFaceUploadDialogProps {
  onComplete: () => void;
}

export function MultiFaceUploadDialog({ onComplete }: MultiFaceUploadDialogProps) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [fileBase64, setFileBase64] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [detectedFaces, setDetectedFaces] = useState<DetectedFace[]>([]);
  const [names, setNames] = useState<Record<number, string>>({});
  const [validating, setValidating] = useState(false);
  const [errors, setErrors] = useState<Record<number, string>>({});
  const [showFullImage, setShowFullImage] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileUpload = async (file: File) => {
    setFile(file);
    setLoading(true);

    // convert file to base64
    const reader = new FileReader();
    reader.onload = (e) => {
      setFileBase64(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    try {
      const formData = new FormData();
      formData.append("file", file, file.name);

      const response = await apiClient("/faces/detect", {
        method: "POST",
        body: formData,
        headers: {}, 
      });

      const data = await response.json();
      setPreviewImage(data.preview_image);
      setDetectedFaces(data.faces);

      const initialNames = data.faces.reduce((acc: Record<number, string>, face: DetectedFace) => {
        acc[face.id] = "";
        return acc;
      }, {});
      setNames(initialNames);
    } catch (error) {
      console.error("Error detecting faces:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleFileUpload(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !detectedFaces.length) return;

    setValidating(true);
    setErrors({});

    try {
      const faces = detectedFaces.map((face) => ({
        id: face.id,
        name: names[face.id],
        bbox: face.bbox,
      }));

      const response = await apiClient("/faces/save-multiple", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_base64: fileBase64,
          faces,
        }),
      });

      const data = await response.json();

      // Check for errors
      const newErrors: Record<number, string> = {};
      data.results.forEach((result: any) => {
        if (!result.success) {
          newErrors[result.id] = result.error;
        }
      });

      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors);
        return;
      }

      // Success - close dialog and refresh
      setOpen(false);
      onComplete();
    } catch (error) {
      console.error("Error saving faces:", error);
    } finally {
      setValidating(false);
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className="flex gap-2 items-center">
            <Upload className="h-4 w-4" />
            Add Face
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Upload Image</DialogTitle>
          </DialogHeader>

          {!previewImage ? (
            <div className="space-y-4">
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragging
                    ? 'border-primary bg-primary/10'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <Input
                  type="file"
                  accept="image/*"
                  onChange={handleFileInputChange}
                  disabled={loading}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center gap-2"
                >
                  <Upload className="h-8 w-8 text-gray-400" />
                  <span className="text-sm text-gray-600">
                    {isDragging
                      ? 'Drop image here'
                      : 'Click or drag image to upload'}
                  </span>
                </label>
              </div>
              {loading && (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Detecting faces...</span>
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative cursor-pointer transition-transform hover:scale-105 h-[50vh]">
                <img 
                  src={`data:image/jpeg;base64,${previewImage}`} 
                  alt="Preview" 
                  className="w-full h-full rounded-lg object-contain"
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-10 transition-opacity flex items-center justify-center">
                  <span className="text-white opacity-0 hover:opacity-100">Click to enlarge</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {detectedFaces.map((face) => (
                  <div key={face.id} className="space-y-2 p-4 border rounded-lg">
                    <Label>Face #{face.id}</Label>
                    <Input
                      value={names[face.id]}
                      onChange={(e) => setNames((prev) => ({ ...prev, [face.id]: e.target.value }))}
                      placeholder="Enter name"
                      required
                    />
                    {errors[face.id] && <p className="text-sm text-red-500">{errors[face.id]}</p>}
                  </div>
                ))}
              </div>

              <Button type="submit" disabled={validating || Object.values(names).some((n) => !n)} className="w-full">
                {validating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Validating...
                  </>
                ) : (
                  "Save Faces"
                )}
              </Button>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Full-size image dialog */}
      {showFullImage && (
        <Dialog open={showFullImage} onOpenChange={setShowFullImage}>
          <DialogContent className="max-w-[90vw] h-screen p-0">
            <DialogHeader className="p-6">
              <DialogTitle>
                <VisuallyHidden>Full size image preview</VisuallyHidden>
              </DialogTitle>
            </DialogHeader>
            <div className="flex items-center justify-center h-[calc(100vh-100px)]">
              <img src={`data:image/jpeg;base64,${previewImage}`} alt="Full size preview" className="max-w-full max-h-full object-contain" />
            </div>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
