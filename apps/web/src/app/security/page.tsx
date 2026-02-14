import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Security",
  description:
    "How pruv protects your data. SHA-256 hashing, Ed25519 signatures, AES-256-GCM encryption, auto-redaction. Security is not a feature. It is the foundation.",
};

export default function SecurityPage() {
  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <div className="section-label">security</div>
          <h1>Security is the foundation.</h1>
          <p>
            pruv is a cryptographic primitive. Security is not a feature added
            on top. It is the entire product.
          </p>
        </div>

        <div className="page-body">
          <h2>Cryptographic verification</h2>
          <p>
            SHA-256 hashing creates tamper-evident chains of state transitions.
            Every entry&apos;s XY proof is computed from the canonical
            representation of the before state (X) and after state (Y), combined
            with the timestamp and link to the previous entry.
          </p>
          <p>
            The chain rule ensures that Entry[N].x == Entry[N-1].y. Any
            modification invalidates all subsequent hashes. Tampering is
            mathematically detectable.
          </p>

          <h2>Data protection</h2>
          <div className="spec-table">
            <div className="spec-row">
              <div className="spec-key">In transit</div>
              <div className="spec-val">
                <span className="highlight">TLS 1.3</span> &mdash; HSTS
                enforced, certificate transparency monitored
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">At rest</div>
              <div className="spec-val">
                <span className="highlight">AES-256-GCM</span> &mdash; keys
                rotated regularly via dedicated KMS
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Hashing</div>
              <div className="spec-val">
                <span className="highlight">SHA-256</span> &mdash; canonical
                JSON, deterministic results
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Signatures</div>
              <div className="spec-val">
                <span className="highlight">Ed25519</span> &mdash;
                non-repudiation, independently verifiable
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">API keys</div>
              <div className="spec-val">
                <span className="highlight">SHA-256 hashed</span> &mdash; never
                stored in plaintext, pv_live_ / pv_test_ prefix
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Secrets</div>
              <div className="spec-val">
                <span className="highlight">Auto-redacted</span> &mdash;
                detected and removed before entering the chain
              </div>
            </div>
          </div>

          <h2>Auto-redaction patterns</h2>
          <p>
            Sensitive data is automatically detected and redacted before it
            enters the chain. Redacted values are replaced with hash commitments.
            The proof remains verifiable after redaction.
          </p>
          <div className="spec-table">
            <div className="spec-row">
              <div className="spec-key">sk_live_*, sk_test_*</div>
              <div className="spec-val">Stripe API keys</div>
            </div>
            <div className="spec-row">
              <div className="spec-key">pv_live_*, pv_test_*</div>
              <div className="spec-val">pruv API keys</div>
            </div>
            <div className="spec-row">
              <div className="spec-key">ghp_*, gho_*, ghs_*</div>
              <div className="spec-val">GitHub tokens</div>
            </div>
            <div className="spec-row">
              <div className="spec-key">AKIA*</div>
              <div className="spec-val">AWS access keys</div>
            </div>
            <div className="spec-row">
              <div className="spec-key">password, secret, token</div>
              <div className="spec-val">Generic secret fields</div>
            </div>
          </div>

          <h2>Infrastructure</h2>
          <div className="spec-table">
            <div className="spec-row">
              <div className="spec-key">DDoS protection</div>
              <div className="spec-val">
                Cloudflare WAF and CDN on all endpoints
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Rate limiting</div>
              <div className="spec-val">
                Sliding window on all API endpoints
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">SOC 2 Type II</div>
              <div className="spec-val">
                Security, availability, and confidentiality controls
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Pen testing</div>
              <div className="spec-val">
                Regular third-party penetration testing and audits
              </div>
            </div>
          </div>

          <h2>Responsible disclosure</h2>
          <p>
            If you discover a security vulnerability in pruv, report it to{" "}
            <a href="mailto:security@pruv.dev">security@pruv.dev</a>. We
            acknowledge reports within 24 hours and provide a fix within 72
            hours for critical issues.
          </p>
        </div>
      </div>
    </div>
  );
}
