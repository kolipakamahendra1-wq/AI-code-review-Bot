import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReview } from "../api.js";
import { FindingList, ScoreRing } from "../components/Findings.jsx";

export default function ReviewDetail() {
  const { id } = useParams();
  const [r, setR] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getReview(id).then(setR).catch((e) => setError(e.message));
  }, [id]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link to="/dashboard" className="text-sm text-muted hover:text-white">Back to dashboard</Link>
      {error && <div className="mt-6 rounded-lg border border-crit/40 bg-crit/10 p-4 text-crit">{error}</div>}
      {!r && !error && <p className="mt-6 text-muted">Loading...</p>}
      {r && (
        <>
          <div className="mt-4 flex items-center gap-5">
            {r.status === "done" && <ScoreRing score={r.score} />}
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                {r.repo ? `${r.repo}#${r.pr_number}` : "Pasted diff"}
              </h1>
              <p className="mt-1 text-muted">
                {r.title && `${r.title} · `}{r.model} · {r.created_at}
              </p>
            </div>
          </div>
          {r.status === "error" ? (
            <div className="mt-6 rounded-lg border border-crit/40 bg-crit/10 p-4 text-crit">
              This review failed: {r.error}
            </div>
          ) : (
            <>
              {r.summary && (
                <p className="mt-6 whitespace-pre-line rounded-lg border border-line bg-panel p-4 text-muted">{r.summary}</p>
              )}
              <div className="mt-8"><FindingList findings={r.findings} /></div>
            </>
          )}
        </>
      )}
    </div>
  );
}
