import { ChainDemo } from "@/components/chain-demo";

export default function HomePage() {
  return (
    <>
      {/* ── Hero ── */}
      <div className="container">
        <div className="hero">
          <div className="hero-label">verification primitive</div>
          <h1>
            Prove what <span className="accent">happened.</span>
          </h1>
          <p className="hero-sub">
            Every operation transforms state. pruv captures the before, the
            after, and creates cryptographic proof that the transformation
            happened.
          </p>
          <div className="install-block">
            <span className="prompt">$</span> pip install{" "}
            <span className="pkg">pruv</span>
          </div>
          <div className="hero-links">
            <a href="https://docs.pruv.dev">docs</a>
            <a href="https://app.pruv.dev">dashboard</a>
            <a href="https://github.com/pruv-dev/pruv">github</a>
          </div>
        </div>
      </div>

      {/* ── The Primitive ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">the primitive</div>
          <h2>X &rarr; Y &rarr; XY</h2>
          <p>
            Hash the state before. Hash the state after. Chain them together.
            Each entry&apos;s X must equal the previous entry&apos;s Y. Break
            one entry, the chain breaks. Verification detects exactly where.
          </p>
          <p>
            This is the entire product. Everything else is built on this rule.
          </p>
        </div>
      </div>

      {/* ── Live Chain ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">try it</div>
          <h2>A chain, running in your browser.</h2>
          <p>
            Click any entry to inspect the state diff. Tamper with one to see
            verification break. Restore to see it heal.
          </p>
          <ChainDemo />
        </div>
      </div>

      {/* ── Two Lines ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">usage</div>
          <h2>Two lines. Full proof.</h2>
          <p>
            Wrap any agent, any function, any workflow. Every action is captured
            with cryptographic proof. No configuration. No setup. Two lines.
          </p>

          <div className="code-block">
            <span className="kw">from</span>{" "}
            <span className="var">pruv</span>{" "}
            <span className="kw">import</span>{" "}
            <span className="fn">xy_wrap</span>
            {"\n\n"}
            <span className="var">wrapped</span>{" "}
            <span className="op">=</span>{" "}
            <span className="fn">xy_wrap</span>(
            <span className="var">my_agent</span>)
            {"\n"}
            <span className="var">result</span>{" "}
            <span className="op">= await</span>{" "}
            <span className="var">wrapped</span>.
            <span className="fn">run</span>(
            <span className="str">&quot;Fix the login bug&quot;</span>)
            {"\n\n"}
            <span className="fn">print</span>(
            <span className="var">result</span>.
            <span className="var">receipt</span>.
            <span className="var">hash</span>)
            {"\n"}
            <span className="cm"># xy_a7f3c28e91b4d&hellip;</span>
            {"\n\n"}
            <span className="fn">print</span>(
            <span className="var">result</span>.
            <span className="var">verified</span>)
            {"\n"}
            <span className="cm">
              # True &mdash; every action independently confirmed
            </span>
          </div>

          <div className="receipt-box">
            <div className="receipt-title">pruv receipt</div>
            <div className="receipt-row">
              <span className="receipt-key">task</span>
              <span className="receipt-val">Fix the login bug</span>
            </div>
            <div className="receipt-row">
              <span className="receipt-key">actions</span>
              <span className="receipt-val">23</span>
            </div>
            <div className="receipt-row">
              <span className="receipt-key">verified</span>
              <span className="receipt-val verified">23/23 &#10003;</span>
            </div>
            <div className="receipt-row">
              <span className="receipt-key">duration</span>
              <span className="receipt-val">3m 42s</span>
            </div>
            <div className="receipt-row">
              <span className="receipt-key">X</span>
              <span className="receipt-val">8f3a1c2e</span>
            </div>
            <div className="receipt-row">
              <span className="receipt-key">Y</span>
              <span className="receipt-val">d4e6f71a</span>
            </div>
            <div className="receipt-row">
              <span className="receipt-key">chain</span>
              <span className="receipt-val verified">
                47 entries &middot; intact
              </span>
            </div>
            <div className="receipt-badge">
              <span className="badge-pill">&#10003; verified by pruv</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Not Logging ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">difference</div>
          <h2>Not logging. Proof.</h2>

          <div className="compare">
            <div className="compare-row">
              <div className="compare-label">Logs</div>
              <div className="compare-val">
                &ldquo;Here&rsquo;s what happened, trust us&rdquo;
              </div>
            </div>
            <div className="compare-row">
              <div className="compare-label">Traces</div>
              <div className="compare-val">
                &ldquo;Here&rsquo;s the flow, trust our database&rdquo;
              </div>
            </div>
            <div className="compare-row">
              <div className="compare-label pruv-label">pruv</div>
              <div className="compare-val pruv-val">
                &ldquo;Here&rsquo;s cryptographic proof &mdash; verify
                yourself&rdquo;
              </div>
            </div>
          </div>

          <p style={{ marginTop: 32 }}>
            Receipts are independently verifiable. No pruv account needed. The
            math works with SHA-256 and Ed25519 &mdash; open standards. Anyone
            can verify a pruv receipt with their own code.
          </p>
        </div>
      </div>

      {/* ── Works Everywhere ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">domains</div>
          <h2>Any system that transforms state.</h2>

          <div className="industry-grid">
            <div className="industry-card">
              <div className="industry-name">AI Agents</div>
              <div className="industry-xy">
                <span className="x-label">X:</span> codebase before agent ran
                <br />
                <span className="y-label">Y:</span> codebase after, every
                change proven
              </div>
            </div>
            <div className="industry-card">
              <div className="industry-name">Infrastructure</div>
              <div className="industry-xy">
                <span className="x-label">X:</span> system state before deploy
                <br />
                <span className="y-label">Y:</span> deployed, verified,
                hash-proven
              </div>
            </div>
            <div className="industry-card">
              <div className="industry-name">Financial</div>
              <div className="industry-xy">
                <span className="x-label">X:</span> account balance before
                <br />
                <span className="y-label">Y:</span> transaction settled, proof
                on chain
              </div>
            </div>
            <div className="industry-card">
              <div className="industry-name">Compliance</div>
              <div className="industry-xy">
                <span className="x-label">X:</span> audit requirements
                <br />
                <span className="y-label">Y:</span> controls verified, evidence
                hashed
              </div>
            </div>
            <div className="industry-card">
              <div className="industry-name">Healthcare</div>
              <div className="industry-xy">
                <span className="x-label">X:</span> patient record state
                <br />
                <span className="y-label">Y:</span> treatment administered,
                chain of custody
              </div>
            </div>
            <div className="industry-card">
              <div className="industry-name">Supply Chain</div>
              <div className="industry-xy">
                <span className="x-label">X:</span> shipment at origin
                <br />
                <span className="y-label">Y:</span> delivered, provenance
                proven
              </div>
            </div>
            <div className="industry-card">
              <div className="industry-name">Legal</div>
              <div className="industry-xy">
                <span className="x-label">X:</span> document version
                <br />
                <span className="y-label">Y:</span> signed revision, edit chain
                intact
              </div>
            </div>
            <div className="industry-card">
              <div className="industry-name">Government</div>
              <div className="industry-xy">
                <span className="x-label">X:</span> public record filed
                <br />
                <span className="y-label">Y:</span> immutable, verifiable by
                anyone
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Install ── */}
      <div className="section">
        <div className="container">
          <div className="section-label">install</div>

          <div className="code-block">
            <span className="cm">
              # primitive only &mdash; zero dependencies
            </span>
            {"\n"}
            <span className="prompt">$</span> pip install{" "}
            <span className="pkg">xycore</span>
            {"\n\n"}
            <span className="cm">
              # full SDK &mdash; scanner, wrapper, checkpoints, cloud
            </span>
            {"\n"}
            <span className="prompt">$</span> pip install{" "}
            <span className="pkg">pruv</span>
          </div>

          <p>
            xycore is zero dependencies. Standard library only. Works offline.
            Works without an account. Works without the cloud. The primitive
            needs nothing.
          </p>
        </div>
      </div>
    </>
  );
}
