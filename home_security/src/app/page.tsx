import { HomePage } from "@/components/HomePage";
import { FaceProvider } from "@/contexts/FaceContext";

export default function Home() {
  return (
    <FaceProvider>
      <HomePage />
    </FaceProvider>
  );
}
