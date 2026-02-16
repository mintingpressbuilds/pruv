"use client";

import { useState } from "react";
import { CodeBlock } from "./code-block";

const USE_CASES = [
  {
    name: "AI Agents",
    code: `agent = pruv.Agent("email-assistant", api_key="pv_live_xxx")

agent.action("read_inbox", {"count": 12})
agent.action("draft_reply", {"to": "sarah@co.com"})
agent.action("send_email", {"to": "sarah@co.com"})

# every action receipted. prove what your agent did.`,
  },
  {
    name: "Payments",
    code: `chain = Chain("order-7291")

chain.add("order_placed", {"items": 3, "total": 189.00})
chain.add("payment_authorized", {"method": "card", "last4": "4242"})
chain.add("payment_captured", {"amount": 189.00})
chain.add("fulfillment_started", {"warehouse": "east"})
chain.add("shipped", {"carrier": "fedex", "tracking": "FX882910"})
chain.add("delivered", {"signed_by": "M. Chen"})

# order-to-delivery. every step proven.`,
  },
  {
    name: "Compliance",
    code: `chain = Chain("access-log-2026-02")

chain.add("record_accessed", {
    "user": "dr.patel",
    "record": "patient-8827",
    "reason": "scheduled-appointment"
})

chain.add("record_updated", {
    "user": "dr.patel",
    "field": "prescription",
    "change_hash": "e7f2a1..."  # redacted content, hashed
})

# HIPAA audit trail. cryptographic. immutable.`,
  },
  {
    name: "CI/CD",
    code: `chain = Chain("deploy-main-4481")

chain.add("commit", {"sha": "a3f8c2e", "author": "kai"})
chain.add("tests_passed", {"suite": "unit", "count": 847, "failures": 0})
chain.add("tests_passed", {"suite": "integration", "count": 124, "failures": 0})
chain.add("build_complete", {"artifact": "app-v2.4.1.tar.gz"})
chain.add("deployed", {"env": "production", "region": "us-east-1"})

# prove the build that went to production. every step.`,
  },
  {
    name: "Supply Chain",
    code: `chain = Chain("shipment-LOT-29174")

chain.add("manufactured", {"facility": "shenzhen-03", "batch": "B-441"})
chain.add("qa_passed", {"inspector": "lin.wang", "specs": "ISO-9001"})
chain.add("shipped", {"port": "shenzhen", "vessel": "ever-forward"})
chain.add("customs_cleared", {"port": "long-beach", "docs": "BOL-8827"})
chain.add("received", {"warehouse": "dallas-07", "condition": "intact"})

# field to shelf. every handoff proven.`,
  },
  {
    name: "Legal",
    code: `chain = Chain("contract-NDA-2026-041")

chain.add("drafted", {"by": "legal@acme.com", "version": 1})
chain.add("reviewed", {"by": "counsel@partner.com", "comments": 3})
chain.add("revised", {"by": "legal@acme.com", "version": 2})
chain.add("signed", {"by": "ceo@acme.com", "method": "docusign"})
chain.add("countersigned", {"by": "ceo@partner.com", "method": "docusign"})
chain.add("executed", {"effective_date": "2026-03-01"})

# chain of custody. every revision. every signature.`,
  },
];

export function UseCaseTabs() {
  const [active, setActive] = useState(0);

  return (
    <div className="uc-tabs">
      <div className="uc-tab-bar">
        {USE_CASES.map((uc, i) => (
          <button
            key={uc.name}
            className={`uc-tab${i === active ? " active" : ""}`}
            onClick={() => setActive(i)}
          >
            {uc.name}
          </button>
        ))}
      </div>
      <CodeBlock code={USE_CASES[active].code} label="python" />
    </div>
  );
}
