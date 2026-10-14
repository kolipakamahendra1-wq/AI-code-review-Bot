import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats, listReviews, reviewPR } from "../api.js";
import { SEV, SEV_ORDER } from "../components/Findings.jsx";

const BAR = { critical: "bg-crit", high: "bg-high", medium: "bg-med", low: "bg-low", info: "bg-info" };

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  const load = () =>
    Promise.all([getStats(), listReviews()])
      .then(([s, r]) => (setStats(s), setRows(r), setError("")))
      .catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setNote("");
    try {
      const r = await reviewPR(url);
      setNote(r.skipped ? "That commit was already reviewed." : `Reviewed. Score ${r.score}/100.`);
      setUrl("");
      load();
    } catch (err) {
      setNote(err.message);
    } finally {
      setBusy(false);
    }
  }

  const total = stats ? Object.values(stats.by_severity).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
      <p className="mt-2 text-muted">Every review the bot has run, from webhooks, the Action and the playground.</p>

      {error && <div className="mt-6 rounded-lg border border-crit/40 bg-crit/10 p-4 text-sm text-crit">{error}</div>}

      {stats && (
        <div className="mt-8 grid gap-4 md:grid-cols-[1fr_1fr_1.6fr]">
          <div className="rounded-xl border border-line bg-panel p-5">
            <p className="text-sm text-muted">Reviews run</p>
            <p className="mt-1 text-4xl font-semibold">{stats.reviews}</p>
          </div>
          <div className="rounded-xl border border-line bg-panel p-5">
            <p className="text-sm text-muted">Average score</p>
            <p className="mt-1 text-4xl font-semibold">{stats.reviews ? stats.avg_score : "-"}</p>
          </div>
          <div className="rounded-xl border border-line bg-panel p-5">
            <p className="text-sm text-muted">{stats.findings} findings by severity</p>
            {total === 0 ? (
              <p className="mt-3 text-sm text-muted">Nothing yet.</p>
            ) : (
              <div className="mt-3 space-y-1.5">
                {SEV_ORDER.filter((s) => stats.by_severity[s]).map((s) => (
                  <div key={s} className="flex items-center gap-3 text-sm">
                    <span className="w-16 text-muted">{s}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded bg-line">
                      <div className={`h-full ${BAR[s]}`} style={{ width: `${(stats.by_severity[s] / total) * 100}%` }} />
                    </div>
                    <span className="w-6 text-right font-mono text-xs">{stats.by_severity[s]}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <form onSubmit={submit} className="mt-8 flex flex-col gap-3 sm:flex-row">
        <label htmlFor="pr" className="sr-only">Pull request URL</label>
        <input id="pr" value={url} onChange={(e) => setUrl(e.target.value)} required
          placeholder="https://github.com/owner/repo/pull/12"
          className="flex-1 rounded-lg border border-line bg-panel px-4 py-2.5 outline-none focus:border-accent" />
        <button disabled={busy} className="rounded-lg bg-accent px-5 py-2.5 font-medium text-ink hover:brightness-110 disabled:opacity-50">
          {busy ? "Reviewing..." : "Review this PR"}
        </button>
      </form>
      {note && <p className="mt-2 text-sm text-muted" role="status">{note}</p>}

      <div className="mt-8 overflow-x-auto rounded-xl border border-line">
        <table className="w-full text-left text-sm">
          <thead className="bg-panel text-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Review</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Findings</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">When</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows?.map((r) => (
              <tr key={r.id} className="hover:bg-white/[0.03]">
                <td className="px-4 py-3">
                  <Link to={`/reviews/${r.id}`} className="font-medium text-accent hover:underline">
                    {r.repo ? `${r.repo}#${r.pr_number}` : "Pasted diff"}
                  </Link>
                  {r.title && <p className="max-w-xs truncate text-muted">{r.title}</p>}
                </td>
                <td className="px-4 py-3 text-muted">{r.source}</td>
                <td className="px-4 py-3">{r.finding_count}</td>
                <td className="px-4 py-3">
                  {r.status === "error" ? <span className="text-crit">failed</span> : r.score}
                </td>
                <td className="px-4 py-3 text-muted">{r.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows && rows.length === 0 && (
          <p className="p-8 text-center text-muted">
            No reviews yet. <Link to="/playground" className="text-accent hover:underline">Review a diff in the playground</Link> to see one here.
          </p>
        )}
        {!rows && !error && <p className="p-8 text-center text-muted">Loading...</p>}
      </div>
    </div>
  );
}
