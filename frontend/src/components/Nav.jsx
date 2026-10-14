import { Link, NavLink } from "react-router-dom";

const link = ({ isActive }) =>
  `rounded-md px-3 py-1.5 text-sm transition-colors ${
    isActive ? "bg-white/10 text-white" : "text-muted hover:text-white"
  }`;

export function Logo() {
  return (
    <span className="grid size-6 place-items-center rounded-md bg-accent text-ink">
      <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M5 12.5l4.5 4.5L19 7" />
      </svg>
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
          <Link to="/playground" className="ml-2 hidden rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-ink hover:brightness-110 sm:block">
            Try it free
          </Link>
        </nav>
      </div>
    </header>
  );
}
