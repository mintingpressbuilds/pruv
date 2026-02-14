import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Simple, transparent pricing. Start free. Scale as you grow.",
};

export default function PricingPage() {
  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <div className="section-label">pricing</div>
          <h1>Start free. Scale as you grow.</h1>
          <p>
            Every plan includes the full XY primitive. Upgrade for more entries,
            longer retention, and team features.
          </p>
        </div>

        <div className="page-body">
          <div className="pricing-grid">
            <div className="pricing-card">
              <div className="pricing-name">Free</div>
              <div className="pricing-price">
                $0<span className="period"></span>
              </div>
              <div className="pricing-desc">
                For personal projects and experimentation.
              </div>
              <ul className="pricing-features">
                <li>1,000 entries/month</li>
                <li>Core XY verification</li>
                <li>SHA-256 hash chains</li>
                <li>Python SDK</li>
                <li>7-day retention</li>
                <li>Community support</li>
              </ul>
              <Link href="https://app.pruv.dev" className="pricing-cta">
                Start Free
              </Link>
            </div>

            <div className="pricing-card highlighted">
              <div className="pricing-name">Pro</div>
              <div className="pricing-price">
                $29<span className="period">/mo</span>
              </div>
              <div className="pricing-desc">
                For professionals and growing projects.
              </div>
              <ul className="pricing-features">
                <li>50,000 entries/month</li>
                <li>Everything in Free</li>
                <li>Checkpoints &amp; snapshots</li>
                <li>Ed25519 signatures</li>
                <li>PDF export &amp; receipts</li>
                <li>Webhook notifications</li>
                <li>90-day retention</li>
                <li>Email support</li>
              </ul>
              <Link href="https://app.pruv.dev" className="pricing-cta primary">
                Start Pro Trial
              </Link>
            </div>

            <div className="pricing-card">
              <div className="pricing-name">Team</div>
              <div className="pricing-price">
                $99<span className="period">/mo</span>
              </div>
              <div className="pricing-desc">
                For teams that need compliance and scale.
              </div>
              <ul className="pricing-features">
                <li>500,000 entries/month</li>
                <li>Everything in Pro</li>
                <li>SSO / SAML integration</li>
                <li>Custom redaction rules</li>
                <li>99.9% uptime SLA</li>
                <li>1-year retention</li>
                <li>Priority support</li>
              </ul>
              <Link href="https://app.pruv.dev" className="pricing-cta">
                Start Team Trial
              </Link>
            </div>

            <div className="pricing-card">
              <div className="pricing-name">Enterprise</div>
              <div className="pricing-price">Custom</div>
              <div className="pricing-desc">
                For organizations with complex requirements.
              </div>
              <ul className="pricing-features">
                <li>Unlimited entries</li>
                <li>Everything in Team</li>
                <li>On-premise deployment</li>
                <li>Air-gapped environments</li>
                <li>Custom integrations</li>
                <li>Dedicated support engineer</li>
                <li>SOC 2 / HIPAA compliance</li>
                <li>Custom SLA</li>
              </ul>
              <a href="mailto:sales@pruv.dev" className="pricing-cta">
                Contact Sales
              </a>
            </div>
          </div>

          <div className="section" style={{ borderTop: "none", paddingTop: 48 }}>
            <div className="section-label">rate limits</div>
            <div className="spec-table">
              <div className="spec-row">
                <div className="spec-key">Free</div>
                <div className="spec-val">60 requests/min</div>
              </div>
              <div className="spec-row">
                <div className="spec-key">Pro</div>
                <div className="spec-val">300 requests/min</div>
              </div>
              <div className="spec-row">
                <div className="spec-key">Team</div>
                <div className="spec-val">1,000 requests/min</div>
              </div>
              <div className="spec-row">
                <div className="spec-key">Enterprise</div>
                <div className="spec-val">Custom</div>
              </div>
            </div>
          </div>

          <h2>Frequently asked</h2>

          <h3>What counts as an entry?</h3>
          <p>
            A single X &rarr; Y state transition record. Each call to xy_wrap or
            proof creation counts as one entry. Verification lookups are free and
            unlimited.
          </p>

          <h3>Can I switch plans?</h3>
          <p>
            Yes. Upgrade or downgrade at any time. Changes take effect
            immediately on upgrade, end of billing cycle on downgrade.
          </p>

          <h3>What happens at the limit?</h3>
          <p>
            New entries are queued and processed when your limit resets. No data
            is lost. We notify you at 80% and 100%.
          </p>

          <h3>Self-hosted option?</h3>
          <p>
            Enterprise customers can deploy on-premise or in air-gapped
            environments. Contact sales.
          </p>

          <h3>Annual billing?</h3>
          <p>
            Yes. 20% discount on annual plans. Contact us to switch.
          </p>
        </div>
      </div>
    </div>
  );
}
