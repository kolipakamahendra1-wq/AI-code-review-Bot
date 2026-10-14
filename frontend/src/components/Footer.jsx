import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-muted">
        <span>PR Sentinel · FastAPI · React · Ollama · GitHub Actions</span>
        <span className="flex gap-4">
          <Link to="/docs" className="hover:text-white">Docs</Link>
          <a href="https://github.com/kolipakamahendra1-wq/ai-code-review-bot" className="hover:text-white">GitHub</a>
        </span>
      </div>
    </footer>
  );
}
