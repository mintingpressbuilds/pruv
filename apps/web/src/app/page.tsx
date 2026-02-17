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
          <h1>
            prove what
            <br />
            <span className="accent">happened.</span>
          </h1>
          <p className="hero-sub">
            Something changed in your system.
            A payment processed. A deploy went out. A workflow ran.
            Records were modified.
          </p>
          <p className="hero-sub hero-sub-dim">
            Your logs say everything went fine.
            <br />
            Can you prove it?
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
            Logs can be edited. Databases can be altered. pruv receipts are
            cryptographically chained &mdash; tamper with one entry and the
            entire chain breaks. Verification tells you exactly where.
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

      {/* ── S4: The Receipt ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">the receipt</div>
          <h2>Every operation produces a receipt.</h2>
          <p>
            Every receipt is cryptographically linked to the one before it.
            The recipient can verify independently. No pruv account. No trust required.
          </p>
          <ReceiptCard />
          <p className="receipt-export-text">
            Export as PDF. Embed as badge. Share as link.
            <br />
            The proof stands on its own.
          </p>
        </div>
      </div>

      {/* ── S5: Who Needs This ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">who needs this</div>
          <h2>You need pruv the moment someone asks a question you can&apos;t answer with proof.</h2>

          <div className="needs-grid">
            <div className="needs-item">
              <h3>&ldquo;What exactly happened between 2am and 6am?&rdquo;</h3>
              <p>
                Something changed in production overnight. The postmortem starts with
                &ldquo;we think what happened was&hellip;&rdquo; and ends with a best guess.
              </p>
              <p className="needs-answer">
                pruv gives you the exact sequence &mdash; every state change, in order,
                cryptographically linked. Not a reconstruction. The actual chain of what happened.
              </p>
            </div>

            <div className="needs-item">
              <h3>&ldquo;Can you prove this was processed correctly?&rdquo;</h3>
              <p>
                Money moved. Records changed. A workflow completed.
                Your system says it went fine. But &ldquo;our system says so&rdquo; isn&apos;t proof &mdash; it&apos;s a claim.
              </p>
              <p className="needs-answer">
                pruv gives you a receipt that a third party can verify independently
                without access to your infrastructure.
              </p>
            </div>

            <div className="needs-item">
              <h3>&ldquo;Who approved this and when?&rdquo;</h3>
              <p>
                A change went out. A transaction was authorized. A document was signed off.
                Now there&apos;s a dispute.
              </p>
              <p className="needs-answer">
                pruv records every approval &mdash; who approved, what they approved, when &mdash;
                with Ed25519 digital signatures. The signer cannot deny it.
              </p>
            </div>

            <div className="needs-item">
              <h3>&ldquo;What did the system do with that data?&rdquo;</h3>
              <p>
                Customer data, patient records, financial information moved through your system.
                A regulator asks you to account for every access and modification.
              </p>
              <p className="needs-answer">
                pruv chains every operation into a tamper-evident record.
                Change one entry, the chain breaks, verification reports exactly where.
              </p>
            </div>

            <div className="needs-item">
              <h3>&ldquo;If this gets audited, are we covered?&rdquo;</h3>
              <p>
                SOX. PCI-DSS. MiFID II. HIPAA. Every compliance framework requires
                provable audit trails. Not log files someone could edit.
              </p>
              <p className="needs-answer">
                Cryptographic proof that an external auditor can verify
                without trusting your infrastructure. That&apos;s pruv.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── S6: Payment Verification ── */}
      <DeeperPayments />

      {/* ── S7: Two Ways In ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">two ways in</div>
          <h2>Wrap anything</h2>
          <CodeBlock
            label="python"
            code={`from pruv import xy_wrap

@xy_wrap
def charge_card(customer_id, amount):
    stripe.charges.create(customer=customer_id, amount=amount)

# every call. automatic receipts. zero changes to your logic.`}
          />

          <h2 className="second-way">Or build a chain</h2>
          <CodeBlock
            label="python"
            code={`from pruv import Chain

chain = Chain("deploy-pipeline")
chain.add("tests_passed", {"suite": "integration", "passed": 142})
chain.add("image_built", {"tag": "v2.4.1", "sha": "a3f8c2e"})
chain.add("deployed", {"env": "production", "region": "us-east-1"})
chain.verify()`}
          />

          <p className="two-ways-note">
            Works with any function, any class, any service, any pipeline.
            <br />
            Also integrates with LangChain, CrewAI, and any agent framework
            if that&apos;s what you&apos;re verifying.
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
