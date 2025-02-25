"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import { Slider } from "./ui/slider";
import { RefreshCcw, Save } from "lucide-react";
import { apiClient } from "@/client";
import { toast } from "sonner";

interface Config {
  esp32_ip: string;
  liveness_threshold: number;
  door_open_delay: number;
  darkness_threshold: number;
  max_flash_intensity: number;
  max_face_detection: number;
  face_detection_threshold: number;
  show_video: number;
}

export function SettingsPage() {
  const [config, setConfig] = useState<Config | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [flashValue, setFlashValue] = useState(0);
  const [servoValue, setServoValue] = useState(0);
  const [doorOpen, setDoorOpen] = useState(false);

  const fetchConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiClient("/config");
      const data = await response.json();
      setConfig(data);
    } catch (error) {
      toast.error("Failed to fetch configuration");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleSave = async () => {
    try {
      setIsLoading(true);
      await apiClient("/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      setIsEditing(false);
      toast.success("Configuration saved successfully");
    } catch (error) {
      toast.error("Failed to save configuration");
    } finally {
      setIsLoading(false);
    }
  };

  const handleControl = async (type: string, value: number | boolean) => {
    try {
      await apiClient("/esp32/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, value }),
      });
    } catch (error) {
      toast.error("Failed to control ESP32 component");
    }
  };

  const handleFlashChange = async (value: number[]) => {
    setFlashValue(value[0]);
    await handleControl("flash", value[0]);
  };

  const handleServoChange = async (value: number[]) => {
    setServoValue(value[0]);
    await handleControl("servo", value[0]);
  };

  const handleDoorToggle = async (checked: boolean) => {
    setDoorOpen(checked);
    await handleControl("door", checked);
  };

  if (!config) return null;

  return (
    <div className="container mx-auto py-8 space-y-8 px-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold mb-2">Settings</h1>
          <p className="text-muted-foreground">Manage system configuration and controls</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchConfig} disabled={isLoading}>
            <RefreshCcw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          {isEditing && (
            <Button onClick={handleSave} disabled={isLoading}>
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>System configuration settings</CardDescription>
            <div className="flex items-center space-x-2">
              <Switch checked={isEditing} onCheckedChange={setIsEditing} id="editing-mode" />
              <Label htmlFor="editing-mode">Edit Mode</Label>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(config).map(([key, value]) => (
              <div key={key} className="space-y-2">
                <Label htmlFor={key}>{key.replace(/_/g, " ").toUpperCase()}</Label>
                <Input
                  id={key}
                  value={value}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev!,
                      [key]: typeof value === "number" ? Number(e.target.value) : e.target.value,
                    }))
                  }
                  disabled={!isEditing}
                  type={typeof value === "number" ? "number" : "text"}
                />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>ESP32 Controls</CardTitle>
            <CardDescription>Manual control of ESP32 components</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Flash Intensity</Label>
              <Slider max={255} step={1} value={[flashValue]} onValueChange={handleFlashChange} />
            </div>

            <div className="space-y-2">
              <Label>Servo Angle</Label>
              <Slider max={180} step={1} value={[servoValue]} onValueChange={handleServoChange} />
            </div>

            <div className="flex items-center space-x-2">
              <Switch checked={doorOpen} onCheckedChange={handleDoorToggle} id="door-control" />
              <Label htmlFor="door-control">Door Control</Label>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
