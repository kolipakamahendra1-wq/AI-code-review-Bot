import { Link, NavLink } from "react-router-dom";
import { ShieldCheck } from "@phosphor-icons/react";

const link = ({ isActive }) =>
  `rounded-md px-3 py-1.5 text-sm transition-colors ${
    isActive ? "bg-white/10 text-white" : "text-muted hover:text-white"
  }`;

export function Logo() {
  return (
    <span className="grid size-6 place-items-center rounded-md bg-accent text-ink">
      <ShieldCheck size={16} weight="bold" />
    </span>
  );
}

export default function Nav() {
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-ink/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <Logo /> PR Sentinel
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/playground" className={link}>Playground</NavLink>
          <NavLink to="/dashboard" className={link}>Dashboard</NavLink>
          <NavLink to="/docs" className={link}>Docs</NavLink>
        </nav>
      </div>
    </header>
  );
}
