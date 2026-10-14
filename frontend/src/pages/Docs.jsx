const Code = ({ children }) => (
  <pre className="mt-3 overflow-x-auto rounded-lg border border-line bg-panel p-4 font-mono text-xs leading-6 text-muted">{children}</pre>
);

const Section = ({ id, title, children }) => (
  <section id={id} className="scroll-mt-20 border-t border-line pt-8">
    <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
    <div className="mt-3 space-y-3 leading-relaxed text-muted">{children}</div>
  </section>
);

const env = [
  ["LLM_PROVIDER", "ollama", "ollama, openai or anthropic"],
  ["CHAT_MODEL", "qwen2.5:3b", "Ollama model name"],
  ["OPENAI_API_KEY / ANTHROPIC_API_KEY", "none", "Only needed for those providers"],
  ["GITHUB_TOKEN", "none", "Reads diffs and posts reviews"],
  ["GITHUB_WEBHOOK_SECRET", "none", "Required for the webhook; requests without a valid signature get a 401"],
  ["ENABLE_RULES", "true", "Run the deterministic rule engine alongside the model"],
  ["MAX_FILES", "20", "Files reviewed per pull request"],
];

export default function Docs() {
  return (
    <div className="mx-auto grid max-w-6xl gap-10 px-4 py-10 lg:grid-cols-[200px_1fr]">
      <nav className="hidden lg:block" aria-label="On this page">
        <ul className="sticky top-24 space-y-2 text-sm text-muted">
          {[["action", "GitHub Action"], ["webhook", "Webhook"], ["config", "Configuration"], ["how", "How it works"], ["limits", "Limits"]].map(([id, t]) => (
            <li key={id}><a href={`#${id}`} className="hover:text-white">{t}</a></li>
          ))}
        </ul>
      </nav>

      <div className="max-w-3xl space-y-10">
        <header>
          <h1 className="text-3xl font-semibold tracking-tight">Documentation</h1>
          <p className="mt-2 text-muted">Two ways to run PR Sentinel. Pick the Action if you don't want to host anything.</p>
        </header>

        <Section id="action" title="GitHub Action">
          <p>Add this workflow to <span className="font-mono text-sm">.github/workflows/review.yml</span>. The job comments on the PR and exits with an error when a finding at or above <span className="font-mono text-sm">fail-on</span> exists.</p>
          <Code>{`on: pull_request
jobs:
  review:
    runs-on: ubuntu-latest
    permissions: { pull-requests: write, contents: read }
    steps:
      - uses: kolipakamahendra1-wq/ai-code-review-bot@v1
        with:
          provider: openai        # or anthropic, ollama
          fail-on: high
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: \${{ secrets.OPENAI_API_KEY }}`}</Code>
          <p>GitHub-hosted runners can't reach a model on your laptop. Use a cloud provider there, or a self-hosted runner with Ollama.</p>
        </Section>

        <Section id="webhook" title="Webhook">
          <p>Run the API, then add a webhook in your repo under Settings, Webhooks. Choose <em>Pull requests</em> events, content type <span className="font-mono text-sm">application/json</span>, and the same secret you set in <span className="font-mono text-sm">GITHUB_WEBHOOK_SECRET</span>.</p>
          <Code>{`payload URL:  https://<your-host>/api/webhooks/github
# local demo: expose port 8020 with a tunnel
npx smee-client --url https://smee.io/<channel> --target http://localhost:8020/api/webhooks/github`}</Code>
        </Section>

        <Section id="config" title="Configuration">
          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel"><tr><th className="p-3 font-medium">Variable</th><th className="p-3 font-medium">Default</th><th className="p-3 font-medium">Purpose</th></tr></thead>
              <tbody className="divide-y divide-line">
                {env.map(([k, d, p]) => (
                  <tr key={k}><td className="p-3 font-mono text-xs text-white">{k}</td><td className="p-3 font-mono text-xs">{d}</td><td className="p-3">{p}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section id="how" title="How it works">
          <Code>{`PR opened -> POST /api/webhooks/github   (HMAC-SHA256 verified)
          -> fetch diff -> parse hunks and line numbers
          -> rules (instant)  +  LLM (per file, JSON output)
          -> validate lines against the diff, dedupe, score
          -> one GitHub review with inline comments
          -> saved to SQLite -> dashboard`}</Code>
          <p>If the model returns a line that isn't part of the diff, the finding is moved to the nearest changed line instead of being dropped, because GitHub rejects comments on lines it can't see. Malformed JSON is retried once. The score starts at 100 and loses points by severity.</p>
        </Section>

        <Section id="limits" title="Limits">
          <p>A 3B model on CPU is slow and will miss subtle bugs, which is why the rule engine exists. Reviews look at one file at a time, so cross-file problems are out of reach. Findings are suggestions: a person still decides what to merge.</p>
        </Section>
      </div>
    </div>
  );
}
