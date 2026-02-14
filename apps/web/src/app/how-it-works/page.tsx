import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How It Works",
  description:
    "The XY primitive. Capture the before, the after, create cryptographic proof. No blockchain. No consensus. Just math.",
};

export default function HowItWorksPage() {
  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <div className="section-label">how it works</div>
          <h1>The XY primitive.</h1>
          <p>
            Every system transforms state. pruv captures the before, the after,
            and generates cryptographic proof that the transition occurred. No
            blockchain. No consensus. Just math.
          </p>
        </div>

        <div className="page-body">
          <h2>The core idea</h2>
          <div className="spec-table">
            <div className="spec-row">
              <div className="spec-key">f(X) = Y</div>
              <div className="spec-val">
                Every function transforms state
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">pruv(f)(X)</div>
              <div className="spec-val">
                = Y + <span className="highlight">XY</span> &mdash; pruv adds
                proof to every transition
              </div>
            </div>
          </div>
          <p>
            XY is a cryptographic record containing hashes of both X and Y, a
            timestamp, an optional Ed25519 signature, and a link to the previous
            record in the chain.
          </p>

          <h2>Step by step</h2>

          <div className="step-list">
            <div className="step-item">
              <div className="step-number">1</div>
              <div className="step-title">Capture X (before state)</div>
              <div className="step-desc">
                When a state transition begins, pruv snapshots the current state.
                This becomes X &mdash; a SHA-256 hash of the before state. X can
                be anything: a database record, a configuration file, an API
                payload.
              </div>
            </div>

            <div className="step-item">
              <div className="step-number">2</div>
              <div className="step-title">Execute transition</div>
              <div className="step-desc">
                Your code runs exactly as it normally would. pruv does not modify
                your business logic, intercept calls, or add middleware. It
                observes the input and the output. Zero performance overhead on
                your hot path.
              </div>
            </div>

            <div className="step-item">
              <div className="step-number">3</div>
              <div className="step-title">Capture Y (after state)</div>
              <div className="step-desc">
                When the function returns, pruv captures the result as Y &mdash;
                the after state, hashed the same way as X. Now pruv has both
                endpoints of the transition.
              </div>
            </div>

            <div className="step-item">
              <div className="step-number">4</div>
              <div className="step-title">Generate XY (proof)</div>
              <div className="step-desc">
                pruv combines X and Y into a single verifiable record: XY. This
                includes hashes of both states, a timestamp, an optional Ed25519
                signature, and a link to the previous entry. The result is a
                tamper-evident proof that the transition occurred.
              </div>
            </div>
          </div>

          <h2>The XY record</h2>
          <div className="code-block">
            <span className="cm">
              {`// Simplified XY record structure`}
            </span>
            {"\n"}
            {`{`}
            {"\n"}
            {`  `}
            <span className="str">&quot;id&quot;</span>
            {`: `}
            <span className="str">&quot;xy_8f3a2b1c&quot;</span>
            {`,`}
            {"\n"}
            {`  `}
            <span className="str">&quot;x_hash&quot;</span>
            {`: `}
            <span className="str">&quot;sha256:a1b2c3d4...&quot;</span>
            {`,`}
            {"\n"}
            {`  `}
            <span className="str">&quot;y_hash&quot;</span>
            {`: `}
            <span className="str">&quot;sha256:e5f6a7b8...&quot;</span>
            {`,`}
            {"\n"}
            {`  `}
            <span className="str">&quot;timestamp&quot;</span>
            {`: `}
            <span className="str">&quot;2025-01-15T10:30:00Z&quot;</span>
            {`,`}
            {"\n"}
            {`  `}
            <span className="str">&quot;signature&quot;</span>
            {`: `}
            <span className="str">&quot;ed25519:...&quot;</span>
            {`,`}
            {"\n"}
            {`  `}
            <span className="str">&quot;prev_entry&quot;</span>
            {`: `}
            <span className="str">&quot;xy_7e2f1a0b&quot;</span>
            {`,`}
            {"\n"}
            {`  `}
            <span className="str">&quot;chain_id&quot;</span>
            {`: `}
            <span className="str">&quot;order_processing&quot;</span>
            {"\n"}
            {`}`}
          </div>

          <h2>The chain rule</h2>
          <p>
            When Y of one transition becomes X of the next, pruv links them into
            an unbreakable chain. Each XY record references the previous one.
          </p>

          <div className="spec-table">
            <div className="spec-row">
              <div className="spec-key">Entry[0].x</div>
              <div className="spec-val">
                <span className="highlight">GENESIS</span>
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Entry[N].x</div>
              <div className="spec-val">
                <span className="highlight">== Entry[N-1].y</span>
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Break one</div>
              <div className="spec-val">
                Chain breaks. Verification detects exactly where.
              </div>
            </div>
          </div>

          <h2>Verification</h2>
          <p>
            Anyone with the XY records can independently verify the proof. No
            special tools, no vendor lock-in, no trust required. Walk the chain,
            recompute every hash, check every link.
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
            {"      "}
            <span className="cm"># 1,247 entries</span>
            {"\n"}
            <span className="fn">print</span>(
            <span className="var">chain</span>.valid)
            {"       "}
            <span className="cm"># True &mdash; every link verified</span>
          </div>

          <h2>Properties</h2>
          <div className="spec-table">
            <div className="spec-row">
              <div className="spec-key">Tamper-evident</div>
              <div className="spec-val">
                Any modification invalidates the hash chain. Tampering is
                mathematically detectable.
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Verifiable</div>
              <div className="spec-val">
                Anyone can verify using standard crypto libraries. No proprietary
                tools required.
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Local-first</div>
              <div className="spec-val">
                Proofs generated locally, synced asynchronously. Works offline.
                Works air-gapped.
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Redaction-safe</div>
              <div className="spec-val">
                Sensitive data redacted while preserving cryptographic proof.
                Hash still verifies.
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Append-only</div>
              <div className="spec-val">
                Records can only be added. The chain is a permanent, ordered log
                of state transitions.
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Language-agnostic</div>
              <div className="spec-val">
                Simple JSON schema. Implement in any language. SHA-256 + Ed25519
                are universal.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
