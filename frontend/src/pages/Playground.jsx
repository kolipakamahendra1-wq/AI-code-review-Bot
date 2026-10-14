import { useEffect, useState } from "react";
import { reviewDiff } from "../api.js";
import { SAMPLES } from "../samples.js";
import { FindingList, ScoreRing } from "../components/Findings.jsx";

const MODES = [
  ["rules", "Instant", "Rule engine only. Results in milliseconds."],
  ["ai", "With AI model", "Rules plus the local model. Takes a few minutes on a laptop CPU."],
];

export default function Playground() {
  const [diff, setDiff] = useState(Object.values(SAMPLES)[0]);
  const [mode, setMode] = useState("rules");
  const [busy, setBusy] = useState(false);
  const [secs, setSecs] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!busy) return;
    setSecs(0);
    const t = setInterval(() => setSecs((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [busy]);

  async function run() {
    setBusy(true);
    setError("");
    try {
      setResult(await reviewDiff(diff, mode));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Playground</h1>
      <p className="mt-2 max-w-xl text-muted">
        Paste a unified diff (the output of <span className="font-mono text-sm">git diff</span>) and see what the reviewer says.
      </p>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <section>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted">Try a sample:</span>
            {Object.entries(SAMPLES).map(([name, text]) => (
              <button key={name} onClick={() => setDiff(text)}
                className="rounded-md border border-line px-2.5 py-1 text-sm text-muted hover:bg-white/5 hover:text-white">
                {name}
              </button>
            ))}
          </div>
          <label htmlFor="diff" className="sr-only">Diff</label>
          <textarea id="diff" value={diff} onChange={(e) => setDiff(e.target.value)} spellCheck={false}
            className="h-96 w-full resize-y rounded-lg border border-line bg-panel p-4 font-mono text-xs leading-5 outline-none focus:border-accent" />

          <fieldset className="mt-4 grid gap-2 sm:grid-cols-2">
            <legend className="sr-only">Review mode</legend>
            {MODES.map(([id, label, hint]) => (
              <label key={id}
                className={`cursor-pointer rounded-lg border p-3 ${mode === id ? "border-accent bg-accent/5" : "border-line hover:bg-white/5"}`}>
                <input type="radio" name="mode" value={id} checked={mode === id} onChange={() => setMode(id)} className="sr-only" />
                <span className="block font-medium">{label}</span>
                <span className="mt-0.5 block text-sm text-muted">{hint}</span>
              </label>
            ))}
          </fieldset>

          <button onClick={run} disabled={busy || !diff.trim()}
            className="mt-4 rounded-lg bg-accent px-5 py-3 font-medium text-ink hover:brightness-110 disabled:opacity-50">
            {busy ? `Reviewing... ${secs}s` : "Review this diff"}
          </button>
        </section>

        <section aria-live="polite">
          {error && (
            <div className="rounded-lg border border-crit/40 bg-crit/10 p-4 text-sm text-crit">
              {error}
              {mode === "ai" && " Start Ollama (ollama serve) or switch to Instant mode."}
            </div>
          )}
          {!result && !error && !busy && (
            <div className="grid h-full min-h-48 place-items-center rounded-lg border border-dashed border-line p-8 text-center text-muted">
              Pick a sample and press Review this diff. Findings appear here.
            </div>
          )}
          {busy && (
            <div className="rounded-lg border border-line bg-panel p-6 text-muted">
              Reading the diff line by line. {mode === "ai" && "A local model is slow on CPU, so this can take a few minutes."}
            </div>
          )}
          {result && !busy && (
            <div>
              <div className="mb-6 flex items-center gap-5 rounded-lg border border-line bg-panel p-5">
                <ScoreRing score={result.score} />
                <div className="min-w-0">
                  <p className="font-medium">
                    {result.findings.length} finding{result.findings.length === 1 ? "" : "s"} in {result.files_reviewed} file
                    {result.files_reviewed === 1 ? "" : "s"}
                  </p>
                  <p className="mt-1 text-sm text-muted">Reviewed by {result.model}</p>
                </div>
              </div>
              <FindingList findings={result.findings} />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
