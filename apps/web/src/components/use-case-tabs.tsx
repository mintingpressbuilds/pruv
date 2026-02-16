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
    code: `from pruv import PaymentChain

ledger = PaymentChain("order-7291", api_key="pv_live_xxx")

ledger.deposit("merchant", 10000.00, source="bank", ref="ACH-4401")
ledger.transfer("merchant", "customer_123", 189.00, ref="pi_3abc")
ledger.transfer("merchant", "customer_456", 64.50, ref="pi_3def")

result = ledger.verify_payments()
# ✓ 2 payments verified · balances proven · every dollar accounted for`,
  },
  {
    name: "Compliance",
    code: `chain = Chain("access-log-2026-02")

chain.add("record_accessed", {
    "user": "dr.patel", "record": "patient-8827",
    "reason": "scheduled-appointment"
})
chain.add("record_updated", {
    "user": "dr.patel", "field": "prescription",
    "change_hash": "e7f2a1..."
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

chain.add("manufactured", {"facility": "shenzhen-03"})
chain.add("qa_passed", {"inspector": "lin.wang"})
chain.add("shipped", {"vessel": "ever-forward"})
chain.add("customs_cleared", {"port": "long-beach"})
chain.add("received", {"warehouse": "dallas-07"})

# field to shelf. every handoff proven.`,
  },
  {
    name: "Legal",
    code: `chain = Chain("contract-NDA-2026-041")

chain.add("drafted", {"by": "legal@acme.com", "v": 1})
chain.add("reviewed", {"by": "counsel@partner.com"})
chain.add("revised", {"by": "legal@acme.com", "v": 2})
chain.add("signed", {"by": "ceo@acme.com"})
chain.add("countersigned", {"by": "ceo@partner.com"})

# every revision. every signature. proven.`,
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
      <CodeBlock key={USE_CASES[active].name} code={USE_CASES[active].code} label="python" />
    </div>
  );
}
