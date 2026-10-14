import { Link } from "react-router-dom";

const diff = [
  [10, " ", "    user = get(user)"],
  [11, "+", `    query = "SELECT * FROM users WHERE name = '" + user + "'"`, true],
  [12, "+", "    rows = db.execute(query)"],
  [13, "+", `    API_KEY = "sk-live-9f8e7d6c5b4a"`],
];

const pipeline = [
  ["A pull request is opened", "GitHub sends a signed webhook. The bot verifies the HMAC signature before doing anything."],
  ["The diff is parsed", "Each file is split into hunks, and every changed line gets its real line number. Lockfiles and binaries are skipped."],
  ["Rules and a model both read it", "Twelve deterministic rules run instantly. A local model adds the judgment calls rules can't make."],
  ["Comments land on the exact line", "Findings are checked against the diff so GitHub accepts them, then posted as one review with a score."],
];

const features = [
  ["Free to run on your own machine", "The default model is Ollama qwen2.5:3b. No account, no API key, no per-review bill, and your code never leaves your network. Switch to OpenAI or Claude with one environment variable."],
  ["Catches the obvious first", "Rules for hardcoded secrets, SQL injection, eval, shell=True and disabled TLS run on every change, so a small model's bad day can't let them slip by."],
  ["Safe to leave on", "Reviews are idempotent per commit, drafts are skipped, and a failed review is recorded instead of crashing the worker."],
  ["Works as a webhook or an Action", "Host the FastAPI service, or drop one workflow file into any repo and gate merges with --fail-on high."],
];

const yaml = `on: pull_request
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: kolipakamahendra1-wq/ai-code-review-bot@v1
        with:
          fail-on: high
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}`;

export default function Landing() {
  return (
    <div>
      <section className="relative overflow-hidden">
        <div className="grid-bg absolute inset-0" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 pb-24 pt-20 lg:grid-cols-[1fr_1.05fr]">
          <div>
            <h1 className="text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl">
              Catch the bug before your teammate has to.
            </h1>
            <p className="mt-6 max-w-md text-lg leading-relaxed text-muted">
              Reviews every pull request the moment it opens, comments on the exact line, and suggests the fix.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link to="/playground" className="rounded-lg bg-accent px-5 py-3 font-medium text-ink hover:brightness-110">
                Review a diff now
              </Link>
              <Link to="/docs" className="rounded-lg border border-line px-5 py-3 hover:bg-white/5">
                Add it to a repo
              </Link>
            </div>
          </div>

          <div className="overflow-hidden rounded-xl border border-line bg-panel shadow-2xl shadow-black/40" aria-label="Example review">
            <div className="flex items-center gap-2 border-b border-line px-4 py-2.5 text-sm">
              <span className="font-mono text-muted">app/auth.py</span>
              <span className="ml-auto text-xs text-ok">+3</span>
            </div>
            <div className="font-mono text-[13px] leading-6">
              {diff.map(([n, sign, code, hit]) => (
                <div key={n}>
                  <div className={`flex ${sign === "+" ? "bg-ok/10" : ""} ${hit ? "flash" : ""}`}>
                    <span className="w-10 shrink-0 select-none pr-3 text-right text-muted">{n}</span>
                    <span className={`w-4 shrink-0 ${sign === "+" ? "text-ok" : "text-muted"}`}>{sign}</span>
                    <span className="overflow-x-auto whitespace-pre pr-3">{code}</span>
                  </div>
                  {hit && (
                    <div className="land mx-3 my-2 rounded-lg border border-crit/40 bg-ink p-3 font-sans text-sm leading-normal">
                      <div className="flex items-center gap-2">
                        <span className="rounded border border-crit/40 bg-crit/10 px-1.5 py-0.5 text-xs font-medium text-crit">critical</span>
                        <span className="font-medium">Possible SQL injection</span>
                      </div>
                      <p className="mt-1.5 text-muted">
                        The query is built by joining a user-supplied string. Anyone can end the quote and run their own SQL.
                      </p>
                      <p className="mt-2 rounded bg-panel p-2 font-mono text-xs text-ok">
                        cursor.execute("SELECT * FROM users WHERE name = %s", (user,))
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20">
        <h2 className="max-w-xl text-3xl font-semibold tracking-tight">From opened PR to inline comments in four steps</h2>
        <ol className="mt-10 grid gap-x-10 gap-y-8 md:grid-cols-2">
          {pipeline.map(([title, body], i) => (
            <li key={title} className="flex gap-4 border-t border-line pt-5">
              <span className="font-mono text-sm text-accent">{i + 1}</span>
              <div>
                <h3 className="font-medium">{title}</h3>
                <p className="mt-1.5 leading-relaxed text-muted">{body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-20">
        <h2 className="max-w-xl text-3xl font-semibold tracking-tight">Built to be left on</h2>
        <dl className="mt-10 divide-y divide-line border-y border-line">
          {features.map(([t, d]) => (
            <div key={t} className="grid gap-2 py-6 md:grid-cols-[1fr_2fr] md:gap-10">
              <dt className="font-medium">{t}</dt>
              <dd className="max-w-2xl leading-relaxed text-muted">{d}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-24">
        <div className="grid items-center gap-8 rounded-2xl border border-line bg-panel p-8 md:grid-cols-2">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">One file in your repo</h2>
            <p className="mt-3 max-w-sm text-muted">
              Add this workflow and every pull request gets reviewed. The job fails the build when a high-severity issue is found.
            </p>
            <Link to="/docs" className="mt-6 inline-block text-accent hover:underline">Read the setup guide</Link>
          </div>
          <pre className="overflow-x-auto rounded-lg border border-line bg-ink p-4 font-mono text-xs leading-6 text-muted">{yaml}</pre>
        </div>
      </section>
    </div>
  );
}
