import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Industries",
  description:
    "Any system that transforms state. pruv adds cryptographic verification to AI agents, infrastructure, finance, healthcare, and more.",
};

const industries = [
  {
    name: "AI Agents",
    x: "codebase before agent ran",
    y: "codebase after, every change proven",
    detail:
      "Wrap any agent with xy_wrap. Every file read, write, API call, and decision becomes a verifiable entry. Ship agents with receipts, not promises.",
  },
  {
    name: "Infrastructure",
    x: "system state before deploy",
    y: "deployed, verified, hash-proven",
    detail:
      "Every deployment is a state transition. pruv captures the config before, the result after, and chains them together. Roll back with proof of what changed.",
  },
  {
    name: "Financial Services",
    x: "account balance before",
    y: "transaction settled, proof on chain",
    detail:
      "Tamper-proof audit trails for every transaction. Meet SOX, PCI-DSS, and regulatory requirements with cryptographic certainty, not trust.",
  },
  {
    name: "Compliance",
    x: "audit requirements",
    y: "controls verified, evidence hashed",
    detail:
      "Generate verifiable evidence for SOC 2, ISO 27001, and HIPAA. Receipts prove controls were executed. Auditors verify independently.",
  },
  {
    name: "Healthcare",
    x: "patient record state",
    y: "treatment administered, chain of custody",
    detail:
      "Verifiable chain of custody for patient records, medication tracking, and clinical data. HIPAA-ready by design. Auto-redaction protects PHI.",
  },
  {
    name: "Supply Chain",
    x: "shipment at origin",
    y: "delivered, provenance proven",
    detail:
      "Track provenance from source to shelf. Every handoff, transformation, and quality check becomes a verifiable record in the chain.",
  },
  {
    name: "Legal",
    x: "document version",
    y: "signed revision, edit chain intact",
    detail:
      "Prove document authenticity and track edit history. Maintain chain of custody for evidence and contracts with cryptographic proof.",
  },
  {
    name: "Government",
    x: "public record filed",
    y: "immutable, verifiable by anyone",
    detail:
      "Transparent, verifiable records for public proceedings, policy changes, and citizen data handling. Anyone can verify. No trust required.",
  },
];

export default function IndustriesPage() {
  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <div className="section-label">industries</div>
          <h1>Any system that transforms state.</h1>
          <p>
            Wherever state changes, pruv can prove it. The primitive is
            universal. The applications are specific.
          </p>
        </div>

        <div className="page-body">
          <div className="industry-grid">
            {industries.map((ind) => (
              <div key={ind.name} className="industry-card">
                <div className="industry-name">{ind.name}</div>
                <div className="industry-xy">
                  <span className="x-label">X:</span> {ind.x}
                  <br />
                  <span className="y-label">Y:</span> {ind.y}
                </div>
              </div>
            ))}
          </div>

          {industries.map((ind) => (
            <div key={ind.name}>
              <h2>{ind.name}</h2>
              <div className="spec-table">
                <div className="spec-row">
                  <div className="spec-key">X (before)</div>
                  <div className="spec-val">{ind.x}</div>
                </div>
                <div className="spec-row">
                  <div className="spec-key">Y (after)</div>
                  <div className="spec-val">
                    <span className="highlight">{ind.y}</span>
                  </div>
                </div>
              </div>
              <p>{ind.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
