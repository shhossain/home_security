import Link from "next/link";
import { Button } from "./ui/button";
import { Home, Settings } from "lucide-react";

export function Sidebar() {
  return (
    <div className="fixed left-0 top-0 h-screen w-16 m-0 flex flex-col bg-background border-r">
      <Link href="/">
        <Button variant="ghost" size="icon" className="w-16 h-16">
          <Home className="h-6 w-6" />
        </Button>
      </Link>
      <Link href="/settings">
        <Button variant="ghost" size="icon" className="w-16 h-16">
          <Settings className="h-6 w-6" />
        </Button>
      </Link>
    </div>
  );
}
