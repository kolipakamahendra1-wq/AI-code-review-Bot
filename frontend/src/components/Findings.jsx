export const SEV = {
  critical: "text-crit border-crit/40 bg-crit/10",
  high: "text-high border-high/40 bg-high/10",
  medium: "text-med border-med/40 bg-med/10",
  low: "text-low border-low/40 bg-low/10",
  info: "text-info border-info/40 bg-info/10",
};
export const SEV_ORDER = ["critical", "high", "medium", "low", "info"];

export function SeverityBadge({ level }) {
  return (
    <span className={`rounded border px-1.5 py-0.5 text-xs font-medium ${SEV[level] || SEV.info}`}>
      {level}
    </span>
  );
}

export function ScoreRing({ score, size = 88 }) {
  const r = 36;
  const c = 2 * Math.PI * r;
  const color = score >= 80 ? "var(--color-ok)" : score >= 50 ? "var(--color-med)" : "var(--color-crit)";
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg viewBox="0 0 88 88" className="absolute inset-0 -rotate-90">
        <circle cx="44" cy="44" r={r} fill="none" stroke="var(--color-line)" strokeWidth="7" />
        <circle cx="44" cy="44" r={r} fill="none" stroke={color} strokeWidth="7" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)} />
      </svg>
      <span className="text-xl font-semibold">{score}</span>
    </div>
  );
}

export function FindingCard({ f }) {
  return (
    <div className="rounded-lg border border-line bg-panel p-4">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge level={f.severity} />
        <span className="text-xs text-muted">{f.category}</span>
        <span className="ml-auto font-mono text-xs text-muted">
          {f.file}:{f.line}
        </span>
      </div>
      <h4 className="mt-2 font-medium">{f.title}</h4>
      <p className="mt-1 text-sm leading-relaxed text-muted">{f.message}</p>
      {f.suggestion && (
        <p className="mt-3 rounded-md border border-line bg-ink p-3 font-mono text-xs leading-relaxed text-ok">
          {f.suggestion}
        </p>
      )}
    </div>
  );
}

export function FindingList({ findings }) {
  if (!findings.length)
    return (
      <div className="rounded-lg border border-ok/30 bg-ok/5 p-6 text-center text-ok">
        No issues found. Ship it.
      </div>
    );
  const byFile = findings.reduce((acc, f) => ((acc[f.file] ||= []).push(f), acc), {});
  return (
    <div className="space-y-6">
      {Object.entries(byFile).map(([file, fs]) => (
        <div key={file}>
          <h3 className="mb-2 font-mono text-sm text-muted">{file}</h3>
          <div className="space-y-3">
            {fs.map((f, i) => <FindingCard key={i} f={f} />)}
          </div>
        </div>
      ))}
    </div>
  );
}
