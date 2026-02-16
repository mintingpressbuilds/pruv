import { HeroChainDemo } from "@/components/hero-chain-demo";
import { CodeBlock } from "@/components/code-block";
import { IntegrationTabs } from "@/components/integration-tabs";
import { AlertDemo } from "@/components/alert-demo";
import { ReceiptCard } from "@/components/receipt-card";
import { CopyInstall } from "@/components/copy-install";

export default function HomePage() {
  return (
    <div className="home">
      {/* ── S1: Hero ── */}
      <div className="container">
        <div className="hero">
          <h1>
            prove what your
            <br />
            AI agent <span className="accent">did.</span>
          </h1>
          <p className="hero-sub">
            Every action. Every tool call. Every message.
            <br />
            Cryptographic receipts your agent can&apos;t fake.
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
          </div>
        </div>
      </div>

      {/* ── S2: The Problem ── */}
      <div className="section">
        <div className="container">
          <p className="problem-text">
            AI agents read your email, send messages, execute code,
            and access your files. You have no proof of what they actually did.
          </p>
          <p className="problem-contrast">
            Logs can be edited. Logs can be deleted. Logs lie.
            <br />
            pruv receipts are cryptographic. They can&apos;t.
          </p>
        </div>
      </div>

      {/* ── S3: Live Code Demo ── */}
      <div className="section">
        <div className="container-wide">
          <div className="section-label">how it looks</div>
          <h2>3 lines. Full proof.</h2>
          <p>
            Wrap any AI agent. Every action gets hashed, chained, and verified.
          </p>
          <HeroChainDemo />
        </div>
      </div>

      {/* ── S4: Decorator ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">even simpler</div>
          <h2>Or just decorate your functions.</h2>
          <p>
            Zero code changes to your logic. Every call gets a cryptographic receipt. Automatically.
          </p>
          <CodeBlock
            label="python"
            code={`@pruv.verified
def send_email(to, subject, body):
    smtp.send(to, subject, body)

# Every call to send_email now has
# a cryptographic receipt. Automatically.`}
          />
        </div>
      </div>

      {/* ── S5: Framework Integrations ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">integrations</div>
          <h2>Works with the tools you already use.</h2>
          <IntegrationTabs />
        </div>
      </div>

      {/* ── S6: What pruv catches ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">anomaly detection</div>
          <h2>pruv doesn&apos;t just record. It watches.</h2>
          <AlertDemo />
          <p className="alert-subtext">
            Anomaly detection on the proof chain itself.
            <br />
            Your agent can&apos;t hide what it did.
          </p>
        </div>
      </div>

      {/* ── S7: Receipt ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">the receipt</div>
          <h2>What a pruv receipt looks like.</h2>
          <p>
            Every action produces a receipt. Every receipt is linked to the one before it.
          </p>
          <ReceiptCard />
        </div>
      </div>

      {/* ── S8: How it Works ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">under the hood</div>
          <h2>How pruv works</h2>

          <div className="step-list">
            <div className="step-item">
              <div className="step-number">1</div>
              <div className="step-title">Your agent performs an action</div>
              <div className="step-desc">
                Read a file, send an email, call an API &mdash; any operation.
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">2</div>
              <div className="step-title">The action data is hashed (SHA-256)</div>
              <div className="step-desc">
                Before state, after state, operation name, timestamp &mdash; all hashed.
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">3</div>
              <div className="step-title">The hash is chained to the previous hash</div>
              <div className="step-desc">
                Each entry&apos;s X must equal the previous entry&apos;s Y. Break one, the chain breaks.
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
            This is the same principle that secures blockchains &mdash; without the blockchain.
            <br />
            No tokens. No mining. No gas fees. Just math.
          </p>
        </div>
      </div>

      {/* ── S9: Install ── */}
      <div className="section section-install">
        <div className="container" style={{ textAlign: "center" }}>
          <CopyInstall />
          <div className="install-links">
            <a href="https://docs.pruv.dev" target="_blank" rel="noopener noreferrer">
              <span className="il-label">docs.pruv.dev</span>
              <span className="il-desc">documentation</span>
            </a>
            <a href="https://app.pruv.dev" target="_blank" rel="noopener noreferrer">
              <span className="il-label">app.pruv.dev</span>
              <span className="il-desc">dashboard</span>
            </a>
            <a href="https://github.com/mintingpressbuilds/pruv" target="_blank" rel="noopener noreferrer">
              <span className="il-label">github</span>
              <span className="il-desc">source code</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
