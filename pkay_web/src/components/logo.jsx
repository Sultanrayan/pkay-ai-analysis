import { Link } from "react-router-dom";
import { cn } from "./ui.jsx";

export default function Logo({ className, asLink = true }) {
  const content = (
    <>
      <img
        src="/logo.jpg"
        alt="Pkay AI"
        className="h-8 w-8 rounded-lg object-cover"
      />
      <span className="text-lg font-extrabold tracking-tight text-white">
        Pkay<span className="text-neutral-500">AI</span>
      </span>
    </>
  );

  if (!asLink) {
    return (
      <span className={cn("flex items-center gap-2.5", className)}>
        {content}
      </span>
    );
  }

  return (
    <Link to="/" className={cn("flex items-center gap-2.5", className)}>
      {content}
    </Link>
  );
}
