import { HeroChainDemo } from "@/components/hero-chain-demo";
import { CodeBlock } from "@/components/code-block";
import { DeeperPayments } from "@/components/deeper-payments";
import { AlertDemo } from "@/components/alert-demo";
import { ReceiptCard } from "@/components/receipt-card";
import { CopyInstall } from "@/components/copy-install";

export default function HomePage() {
  return (
    <div className="home">
      {/* ── S1: Hero ── */}
      <div className="container">
        <div className="hero">
          <p className="hero-category">digital verification infrastructure.</p>
          <h1>
            The digital world has no
            <br />
            verification <span className="accent">layer.</span>
          </h1>
          <p className="hero-sub">
            Every system &mdash; every pipeline, every payment, every agent,
            every workflow &mdash; runs on trust. Trust in logs. Trust in
            databases. Trust in whoever ran the process.
          </p>
          <p className="hero-sub hero-sub-dim">
            That trust is manufactured. State changed. Prove it.
          </p>
          <div className="hero-actions">
            <div className="install-block">
              <span className="prompt">$</span> pip install{" "}
              <span className="pkg">pruv</span>
            </div>
            <a
              href="https://docs.pruv.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="hero-docs-link"
            >
              view docs &rarr;
            </a>
            <a
              href="https://app.pruv.dev/scan"
              target="_blank"
              rel="noopener noreferrer"
              className="hero-docs-link"
            >
              scan a repo &rarr;
            </a>
          </div>
        </div>
      </div>

      {/* ── S2: The Gap ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">the gap</div>
          <h2>Every system logs what happened. No system proves it.</h2>

          <div className="compare">
            <div className="compare-row">
              <div className="compare-label">Logs</div>
              <div className="compare-val">&ldquo;Here&apos;s what happened, trust us&rdquo;</div>
            </div>
            <div className="compare-row">
              <div className="compare-label">Traces</div>
              <div className="compare-val">&ldquo;Here&apos;s the flow, trust our database&rdquo;</div>
            </div>
            <div className="compare-row">
              <div className="compare-label pruv-label">pruv</div>
              <div className="compare-val pruv-val">&ldquo;Here&apos;s cryptographic proof &mdash; verify it yourself&rdquo;</div>
            </div>
          </div>

          <p className="gap-text">
            Logs can be edited. Databases can be altered. pruv chains are
            cryptographically linked &mdash; tamper with one entry and the
            chain breaks. Verification reports exactly where.
          </p>
        </div>
      </div>

      {/* ── S3: The protocol in 30 seconds ── */}
      <div className="section">
        <div className="container-wide">
          <div className="section-label">the protocol in 30 seconds</div>
          <h2>Create a chain. Add entries. Verify.</h2>
          <HeroChainDemo />
        </div>
      </div>

      {/* ── S4: Scan ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">pruv.scan</div>
          <h2>Hash every file. Get a verified fingerprint.</h2>
          <p>
            Hash every file in a directory or repository. Produces a deterministic
            project state fingerprint. Prove exactly what your codebase looked like
            at any moment.
          </p>
          <CodeBlock
            label="terminal"
            code={`$ pruv scan ./my-project

  Services (3)
    ✓ FastAPI backend     python   port 8000
    ✓ Next.js frontend    typescript
    ✓ Stripe webhook      external

  Connections
    frontend → backend    via NEXT_PUBLIC_API_URL
    backend → Supabase    via DATABASE_URL
    backend → Stripe      via STRIPE_SECRET_KEY

  Env Vars
    9 defined · 1 missing · 2 shared

  Graph hash: a7f3c28e91b4`}
          />
          <p>
            No code changes. No integration. Point it at a codebase
            and get a verified architecture map.
          </p>
        </div>
      </div>

      {/* ── S5: Identity ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">pruv.identity</div>
          <h2>A passport for AI agents.</h2>
          <p>
            Register with declared owner, permissions, and validity period.
            Every action checked against scope. Receipt shows what it did
            and whether it stayed in bounds.
          </p>
          <CodeBlock
            label="python"
            code={`from pruv.identity import register, act, verify

agent = register(
    name="deploy-bot",
    agent_type="openclaw",
    owner="ops-team",
    scope=["file.read", "system.execute"],
    valid_until="2026-06-01"
)

act(agent, "deploy", {"env": "production", "tag": "v2.4.1"})
receipt = verify(agent)   # in-scope, signed, tamper-evident`}
          />
        </div>
      </div>

      {/* ── S6: Provenance ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">pruv.provenance</div>
          <h2>Chain of custody for any digital artifact.</h2>
          <p>
            Origin captured. Every modification recorded &mdash; who touched it,
            why, what it looked like before and after. Tamper-evident.
            Independently verifiable.
          </p>
          <CodeBlock
            label="python"
            code={`from pruv.provenance import track

doc = track("contract-v3.pdf", origin="legal-team")
doc.modify(actor="counsel", reason="clause 4.2 revision")
doc.modify(actor="cfo", reason="final approval")
doc.export_receipt()   # full chain of custody, verifiable`}
          />
        </div>
      </div>

      {/* ── S7: Checkpoint ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">pruv.checkpoint</div>
          <h2>Time travel for any system state.</h2>
          <p>
            Every chain entry captures what your system was at that exact moment.
            Open any entry, see state before and after, restore to any prior
            verified state. Recovery is no longer expensive or uncertain.
          </p>
          <CodeBlock
            label="python"
            code={`from pruv import CheckpointManager

manager = CheckpointManager(chain, project_dir="./my-project")

checkpoint = manager.create("before-refactor")

# Something goes wrong — restore to verified state
manager.restore(checkpoint.id)

# Or undo the last action
manager.quick_undo()`}
          />
        </div>
      </div>

      {/* ── S8: Receipts ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">pruv.receipts</div>
          <h2>Every operation produces a receipt.</h2>
          <p>
            Not a log. Not an assertion. Proof anyone can verify independently
            &mdash; no account required, no trust required in pruv.
            Export as PDF. Share via link. Embed as badge.
          </p>
          <ReceiptCard />
          <p className="receipt-export-text">
            The proof stands on its own.
          </p>
        </div>
      </div>

      {/* ── S8: Anomaly Detection ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">anomaly detection</div>
          <h2>pruv doesn&apos;t just record. It watches.</h2>
          <AlertDemo />
          <p className="alert-subtext">
            Anomaly detection runs on the proof chain itself.
            <br />
            Set severity thresholds. Get webhook alerts.
            <br />
            If something unusual happened, you&apos;ll know &mdash; and you&apos;ll have the proof.
          </p>
        </div>
      </div>

      {/* ── S9: How the Protocol Works ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">how the protocol works</div>
          <h2>Every operation transforms state. pruv captures both sides.</h2>

          <div className="step-list">
            <div className="step-item">
              <div className="step-number">1</div>
              <div className="step-title">Something happens in your system</div>
              <div className="step-desc">
                A payment, a deploy, a data change &mdash; any operation that transforms state.
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">2</div>
              <div className="step-title">The state before and after are hashed (SHA-256)</div>
              <div className="step-desc">
                Before state, after state, operation, timestamp &mdash; all hashed together.
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">3</div>
              <div className="step-title">The hash includes the previous entry&apos;s hash</div>
              <div className="step-desc">
                Creating a chain. Break one entry, the chain breaks.
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">4</div>
              <div className="step-title">A signed receipt is stored</div>
              <div className="step-desc">
                Ed25519 digital signature. Independently verifiable by anyone.
              </div>
            </div>
          </div>

          <p className="how-note">
            Same principle that secures blockchains.
            <br />
            <strong>Without the blockchain.</strong>
          </p>
          <p className="how-note">
            No tokens. No mining. No gas fees. No consensus.
            <br />
            Just math.
          </p>
        </div>
      </div>

      {/* ── S10: Cloud Optional ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">cloud optional</div>
          <h2>The protocol runs locally. Zero dependencies. Works offline. Works forever.</h2>
          <p>
            The cloud adds the dashboard, team collaboration,
            shareable receipts, and PDF export. It&apos;s optional.
          </p>
          <div className="cloud-install">
            <CodeBlock
              label="bash"
              code={`$ pip install xycore    # protocol only, zero deps
$ pip install pruv      # full SDK with cloud`}
            />
          </div>
          <p className="protocol-line">
            The protocol belongs to nobody. The infrastructure is the product.
          </p>
        </div>
      </div>

      {/* ── S11: Bottom CTA ── */}
      <div className="section section-cta">
        <div className="container" style={{ textAlign: "center" }}>
          <h2 className="cta-headline">State changed. Prove it.</h2>
          <CopyInstall />
          <div className="install-links">
            <a href="https://docs.pruv.dev" target="_blank" rel="noopener noreferrer">
              <span className="il-label">docs.pruv.dev</span>
              <span className="il-desc">get started</span>
            </a>
            <a href="https://app.pruv.dev" target="_blank" rel="noopener noreferrer">
              <span className="il-label">app.pruv.dev</span>
              <span className="il-desc">dashboard</span>
            </a>
            <a href="https://github.com/mintingpressbuilds/pruv" target="_blank" rel="noopener noreferrer">
              <span className="il-label">github</span>
              <span className="il-desc">source</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
