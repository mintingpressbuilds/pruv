import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How It Works",
  description:
    "Every system transforms state. pruv captures both sides and generates cryptographic proof. No blockchain. No consensus. Just math.",
};

export default function HowItWorksPage() {
  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <h1>How pruv works</h1>
          <p>
            Every system transforms state. pruv captures the before, the after,
            and generates cryptographic proof that the transition occurred.
          </p>
          <p>
            No blockchain. No consensus. Just math.
          </p>
        </div>

        <div className="page-body">
          <h2>The idea in one sentence</h2>
          <p>
            Your system does work. pruv proves the work happened.
          </p>
          <div className="spec-table">
            <div className="spec-row">
              <div className="spec-key">Your function</div>
              <div className="spec-val">
                <span className="highlight">f(X) = Y</span>
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">With pruv</div>
              <div className="spec-val">
                <span className="highlight">pruv(f)(X) = Y + XY</span>
              </div>
            </div>
          </div>
          <p>
            X is the state before. Y is the state after. XY is the proof.
          </p>
          <p>
            That&apos;s the entire protocol.
          </p>

          <h2>What&apos;s inside an XY record</h2>
          <p>
            XY is a single verifiable record that contains everything needed
            to prove a state transition occurred:
          </p>
          <ul className="hiw-list">
            <li><strong>X hash</strong> &mdash; SHA-256 of the state before</li>
            <li><strong>Y hash</strong> &mdash; SHA-256 of the state after</li>
            <li><strong>Timestamp</strong> &mdash; when the transition happened</li>
            <li><strong>Signature</strong> &mdash; optional Ed25519, proving who performed it</li>
            <li><strong>Previous entry</strong> &mdash; link to the last XY record in the chain</li>
          </ul>
          <div className="code-block">
            <span className="cm">{`// Simplified XY record structure`}</span>
            {"\n"}
            {`{`}
            {"\n"}
            {`  `}<span className="str">&quot;id&quot;</span>{`: `}<span className="str">&quot;xy_8f3a2b1c&quot;</span>{`,`}
            {"\n"}
            {`  `}<span className="str">&quot;x_hash&quot;</span>{`: `}<span className="str">&quot;sha256:a1b2c3d4...&quot;</span>{`,`}
            {"\n"}
            {`  `}<span className="str">&quot;y_hash&quot;</span>{`: `}<span className="str">&quot;sha256:e5f6a7b8...&quot;</span>{`,`}
            {"\n"}
            {`  `}<span className="str">&quot;timestamp&quot;</span>{`: `}<span className="str">&quot;2025-01-15T10:30:00Z&quot;</span>{`,`}
            {"\n"}
            {`  `}<span className="str">&quot;signature&quot;</span>{`: `}<span className="str">&quot;ed25519:...&quot;</span>{`,`}
            {"\n"}
            {`  `}<span className="str">&quot;prev_entry&quot;</span>{`: `}<span className="str">&quot;xy_7e2f1a0b&quot;</span>{`,`}
            {"\n"}
            {`  `}<span className="str">&quot;chain_id&quot;</span>{`: `}<span className="str">&quot;order_processing&quot;</span>
            {"\n"}
            {`}`}
          </div>
          <p>
            Anyone with this record and the original data can recompute the hashes
            and confirm the proof. No special tools. No pruv account. Standard crypto
            libraries in any language.
          </p>

          <h2>How a chain forms</h2>
          <p>
            When Y of one transition becomes X of the next, pruv links them automatically.
          </p>
          <div className="code-block chain-diagram-block">
{`Entry 0          Entry 1          Entry 2
┌──────────┐     ┌──────────┐     ┌──────────┐
│ X: -      │────▶│ X: Y₀    │────▶│ X: Y₁    │
│ Y: Y₀    │     │ Y: Y₁    │     │ Y: Y₂    │
│ XY: h₀   │     │ XY: h₁   │     │ XY: h₂   │
└──────────┘     └──────────┘     └──────────┘`}
          </div>
          <p>
            Each entry includes the previous entry&apos;s hash. Change one entry
            anywhere in the chain and every entry after it becomes invalid.
            Verification walks the chain and tells you exactly where it broke.
          </p>

          <h2>Step by step</h2>

          <div className="step-list">
            <div className="step-item">
              <div className="step-number">1</div>
              <div className="step-title">Capture X</div>
              <div className="step-desc">
                When a state transition begins, pruv snapshots the current state
                and hashes it. This becomes X. It can be anything &mdash; a database
                record, a file, a balance, an API payload, a configuration.
              </div>
            </div>

            <div className="step-item">
              <div className="step-number">2</div>
              <div className="step-title">Your code runs</div>
              <div className="step-desc">
                pruv does not modify your logic, intercept calls, or add middleware.
                Your function executes exactly as it normally would.
              </div>
            </div>

            <div className="step-item">
              <div className="step-number">3</div>
              <div className="step-title">Capture Y</div>
              <div className="step-desc">
                When the function returns, pruv captures the result and hashes it.
                Now it has both endpoints of the transition.
              </div>
            </div>

            <div className="step-item">
              <div className="step-number">4</div>
              <div className="step-title">Generate XY</div>
              <div className="step-desc">
                pruv combines X and Y into a single verifiable record &mdash; the XY proof.
                It links this record to the previous entry in the chain.
                If signing is enabled, it applies an Ed25519 signature.
              </div>
            </div>
          </div>

          <p className="how-note">
            One proof per state transition. Chained to everything before it.
          </p>

          <h2>Verification</h2>
          <p>
            Anyone can verify. Walk the chain, recompute every hash, check every link.
          </p>
          <div className="code-block">
            <span className="kw">from</span>{" "}
            <span className="var">pruv</span>{" "}
            <span className="kw">import</span>{" "}
            <span className="fn">verify</span>
            {"\n\n"}
            <span className="cm"># Verify a single entry</span>
            {"\n"}
            <span className="var">result</span>{" "}
            <span className="op">=</span>{" "}
            <span className="fn">verify</span>(
            <span className="str">&quot;order_processing&quot;</span>,{" "}
            entry_id=<span className="str">&quot;xy_8f3a2b1c&quot;</span>)
            {"\n"}
            <span className="fn">print</span>(
            <span className="var">result</span>.valid)
            {"       "}
            <span className="cm"># True</span>
            {"\n\n"}
            <span className="cm"># Verify an entire chain</span>
            {"\n"}
            <span className="var">chain</span>{" "}
            <span className="op">=</span>{" "}
            <span className="fn">verify</span>(
            <span className="str">&quot;order_processing&quot;</span>,{" "}
            full_chain=<span className="var">True</span>)
            {"\n"}
            <span className="fn">print</span>(
            <span className="var">chain</span>.length)
            {"       "}
            <span className="cm"># 1,247 entries</span>
            {"\n"}
            <span className="fn">print</span>(
            <span className="var">chain</span>.valid)
            {"        "}
            <span className="cm"># True &mdash; every link intact</span>
          </div>
          <p>
            No proprietary tools. No vendor dependency. SHA-256 and Ed25519
            are implemented in every language on every platform.
            If you can compute a hash, you can verify a pruv chain.
          </p>

          <h2>Properties</h2>

          <div className="properties-list">
            <div className="property-item">
              <div className="property-name">Tamper-evident</div>
              <div className="property-desc">
                Any modification invalidates the hash chain.
                Tampering is mathematically detectable.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">Independently verifiable</div>
              <div className="property-desc">
                Anyone can verify using standard crypto libraries.
                No proprietary tools. No pruv account required.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">Local-first</div>
              <div className="property-desc">
                Proofs generated on your machine, synced asynchronously.
                Works offline. Works air-gapped.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">Append-only</div>
              <div className="property-desc">
                Records can only be added, never modified.
                The chain is a permanent, ordered record of state transitions.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">Redaction-safe</div>
              <div className="property-desc">
                Sensitive data can be redacted while preserving cryptographic proof.
                The hash still verifies.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">Language-agnostic</div>
              <div className="property-desc">
                Simple JSON schema. SHA-256 + Ed25519 are universal.
                Implement in any language.
              </div>
            </div>
          </div>

          <h2>What pruv covers</h2>

          <div className="properties-list">
            <div className="property-item">
              <div className="property-name">pruv.scan</div>
              <div className="property-desc">
                Hash every file in a directory or repository. Produces a deterministic
                project state fingerprint. Prove exactly what your codebase looked like
                at any moment.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">pruv.identity</div>
              <div className="property-desc">
                A passport for AI agents. Register with declared owner, permissions,
                and validity period. Every action checked against scope. Receipt shows
                what it did and whether it stayed in bounds.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">pruv.provenance</div>
              <div className="property-desc">
                Chain of custody for any digital artifact. Origin captured. Every
                modification recorded &mdash; who touched it, why, what it looked like
                before and after. Tamper-evident. Independently verifiable.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">pruv.checkpoint</div>
              <div className="property-desc">
                Time travel for any system state. Every chain entry captures what your
                system was at that exact moment. Open any entry, see state before and
                after, restore to any prior verified state. Recovery is no longer
                expensive or uncertain.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">pruv.receipts</div>
              <div className="property-desc">
                Every operation produces a receipt. Not a log. Not an assertion. Proof
                anyone can verify independently &mdash; no account required, no trust
                required in pruv. Export as PDF. Share via link. Embed as badge.
              </div>
            </div>
          </div>

          <h2>Framework integrations</h2>
          <p>
            Dedicated packages for every major AI agent framework. Install, wrap, ship.
            Every action recorded automatically. No manual logging. One line of code.
          </p>

          <div className="properties-list">
            <div className="property-item">
              <div className="property-name">pruv-langchain</div>
              <div className="property-desc">
                Hooks into LangChain&apos;s native callback system. Records every tool call,
                LLM invocation, chain execution, and agent action. Wrap with
                LangChainWrapper &mdash; your agent code stays unchanged.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">pruv-crewai</div>
              <div className="property-desc">
                Intercepts CrewAI lifecycle events &mdash; crew kickoff, task execution,
                agent handoffs, tool usage. Wrap with CrewAIWrapper &mdash; every crew
                run produces a verified receipt.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">pruv-openai</div>
              <div className="property-desc">
                Implements the OpenAI Agents SDK TracingProcessor protocol. Records tool
                calls, guardrail checks, agent handoffs, and LLM calls. Wrap with
                OpenAIAgentWrapper &mdash; automatic scope detection from span types.
              </div>
            </div>
            <div className="property-item">
              <div className="property-name">pruv-openclaw</div>
              <div className="property-desc">
                Config-driven plugin with automatic scope mapping. Hooks into
                before_action and after_action lifecycle. File reads, writes, executions
                &mdash; all scope-checked and chained.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
