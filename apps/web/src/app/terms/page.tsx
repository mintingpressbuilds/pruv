import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "Terms of Service for the pruv platform, API, SDK, and website.",
};

export default function TermsPage() {
  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <div className="section-label">terms</div>
          <h1>Terms of Service</h1>
          <p>Last updated: January 15, 2025</p>
        </div>

        <div className="page-body">
          <h2>1. Acceptance of terms</h2>
          <p>
            By accessing or using pruv (the &ldquo;Service&rdquo;), including
            the xycore library, pruv SDK, cloud API, dashboard, and
            documentation, you agree to be bound by these Terms of Service. If
            you do not agree, do not use the Service.
          </p>

          <h2>2. Service description</h2>
          <p>
            pruv provides cryptographic verification infrastructure for state
            transitions. The Service includes chain storage, verification,
            receipt generation, digital signatures, auto-redaction, and related
            features as described in our documentation.
          </p>

          <h2>3. Usage limits</h2>
          <p>
            Each plan has specific rate limits and monthly entry quotas.
          </p>
          <div className="spec-table">
            <div className="spec-row">
              <div className="spec-key">Free</div>
              <div className="spec-val">
                60 req/min, 1,000 entries/month
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Pro</div>
              <div className="spec-val">
                300 req/min, 50,000 entries/month
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Team</div>
              <div className="spec-val">
                1,000 req/min, 500,000 entries/month
              </div>
            </div>
            <div className="spec-row">
              <div className="spec-key">Enterprise</div>
              <div className="spec-val">Custom limits per agreement</div>
            </div>
          </div>
          <p>
            Exceeding your quota will result in entries being queued until your
            limit resets. No data is lost.
          </p>

          <h2>4. API keys and security</h2>
          <p>
            You are responsible for keeping your API keys secure. Keys with the
            pv_live_ prefix provide production access. Keys with the pv_test_
            prefix provide testing access. Compromised keys should be revoked
            immediately through the dashboard. You are responsible for all
            activity under your API keys.
          </p>

          <h2>5. Data ownership</h2>
          <p>
            You retain full ownership of all data submitted to pruv. We do not
            claim ownership of your chains, entries, or associated state data. We
            will not access, use, or disclose your data except as necessary to
            provide the Service, as required by law, or with your explicit
            consent.
          </p>

          <h2>6. Open source</h2>
          <p>
            The xycore package is released under the MIT License. The pruv SDK is
            released under the MIT License. Use of the cloud service
            (api.pruv.dev) is governed by these Terms. The open source licenses
            apply only to the software itself, not to the hosted service.
          </p>

          <h2>7. Service level</h2>
          <p>
            Team and Enterprise plans include a Service Level Agreement (SLA)
            with guaranteed uptime. Free and Pro plans are provided on a
            best-effort basis.
          </p>

          <h2>8. Termination</h2>
          <p>
            Either party may terminate at any time. Upon termination, you may
            export your data via the API or CLI. Data will be retained for 30
            days after account closure, after which it will be permanently
            deleted.
          </p>

          <h2>9. Limitation of liability</h2>
          <p>
            To the maximum extent permitted by applicable law, pruv shall not be
            liable for any indirect, incidental, special, consequential, or
            punitive damages, or any loss of profits or revenues. Our total
            liability shall not exceed the amount you paid us in the twelve
            months preceding the claim.
          </p>

          <h2>10. Contact</h2>
          <p>
            For questions about these Terms of Service, contact{" "}
            <a href="mailto:legal@pruv.dev">legal@pruv.dev</a>.
          </p>
        </div>
      </div>
    </div>
  );
}
