import { HeroChainDemo } from "@/components/hero-chain-demo";
import { CodeBlock } from "@/components/code-block";
import { UseCaseTabs } from "@/components/use-case-tabs";
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
            operational proof
            <br />
            for any <span className="accent">system.</span>
          </h1>
          <p className="hero-sub">
            Create a chain. Add entries. Every entry is hashed
            and linked to the one before it. Tamper with any entry
            and the chain breaks. That&apos;s it. That&apos;s the protocol.
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

      {/* ── S2: The protocol in 30 seconds ── */}
      <div className="section">
        <div className="container-wide">
          <div className="section-label">the protocol in 30 seconds</div>
          <h2>Create a chain. Add entries. Verify.</h2>
          <HeroChainDemo />
        </div>
      </div>

      {/* ── S3: Works everywhere ── */}
      <div className="section">
        <div className="container-wide">
          <div className="section-label">works everywhere</div>
          <h2>One protocol. Every industry.</h2>
          <p>
            Real code for real use cases. pruv is not an AI tool. It&apos;s a verification protocol that works anywhere state changes.
          </p>
          <UseCaseTabs />
        </div>
      </div>

      {/* ── S4: Decorator ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">even simpler</div>
          <h2>Already have functions? Just decorate them.</h2>
          <CodeBlock
            label="python"
            code={`import pruv
pruv.init("my-system", api_key="pv_live_xxx")

@pruv.verified
def charge_card(customer_id, amount):
    stripe.charges.create(customer=customer_id, amount=amount)

@pruv.verified
def send_notification(user, message):
    twilio.messages.create(to=user.phone, body=message)

@pruv.verified
def update_record(record_id, data):
    db.records.update(record_id, data)

# every call. every function. automatic receipts.
# zero changes to your existing logic.`}
          />
        </div>
      </div>

      {/* ── S5: Framework Integrations ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">integrations</div>
          <h2>Plugs into what you already use.</h2>
          <IntegrationTabs />
        </div>
      </div>

      {/* ── S6: What happens when something goes wrong ── */}
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
            Your systems can&apos;t hide what they did.
          </p>
        </div>
      </div>

      {/* ── S7: Receipt ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">the receipt</div>
          <h2>What a pruv receipt looks like.</h2>
          <p>
            Every entry produces a receipt. Every receipt is linked to the one before it.
          </p>
          <ReceiptCard />
        </div>
      </div>

      {/* ── S8: How it Works ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">how it works</div>
          <h2>how pruv works</h2>

          <div className="step-list">
            <div className="step-item">
              <div className="step-number">1</div>
              <div className="step-title">Something happens in your system</div>
              <div className="step-desc">
                A payment, a deployment, an agent action &mdash; any event.
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">2</div>
              <div className="step-title">The event data is hashed (SHA-256)</div>
              <div className="step-desc">
                Before state, after state, operation, timestamp &mdash; all hashed.
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">3</div>
              <div className="step-title">The hash includes the previous entry&apos;s hash</div>
              <div className="step-desc">
                Each receipt is linked to every receipt before it. Break one, the chain breaks.
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
              <span className="il-desc">source</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
