"use client";

import { IndustryPage } from "@/components/industry-page";

export default function GovernmentIndustryPage() {
  return (
    <IndustryPage
      icon={
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
        </svg>
      }
      title="Government"
      subtitle="Public trust requires provable transparency. pruv creates verifiable records of government processes, policy changes, and citizen data handling that anyone can independently verify."
      problem={{
        title: "The transparency deficit",
        description:
          "Government operations require public accountability, but current record-keeping systems are opaque, fragile, and difficult to independently verify. Citizens and oversight bodies must trust that records have not been altered, but have no way to verify this trust.",
        points: [
          "Public records can be altered without detection",
          "FOIA responses cannot be verified for completeness or authenticity",
          "Policy changes and legislative amendments lack verifiable history",
          "Voter registration and election systems need provable integrity",
          "Permitting and licensing processes have no tamper-evident audit trail",
          "Inter-agency data sharing lacks transparency and accountability",
        ],
      }}
      solution={{
        title: "Provable public accountability.",
        description:
          "pruv makes every government action a verifiable record. Policy changes, permit decisions, record modifications, and data access events all become cryptographic proofs that citizens and oversight bodies can independently verify.",
        xLabel: "Record/policy before",
        yLabel: "Record/policy after",
        example:
          'Example: X = {permit: "P-2024-0001", status: "under_review"} \u2192 Y = {permit: "P-2024-0001", status: "approved", approved_by: "Dept. of Planning"}',
      }}
      codeExample={{
        filename: "permit_system.py",
        code: `from pruv import xy_wrap, checkpoint

@xy_wrap(
    chain="building_permits",
    sign=True,
    redact=["applicant_ssn", "applicant_phone"]
)
def process_permit_application(
    permit_id: str,
    decision: dict,
    reviewer: dict
) -> dict:
    # X = current permit state

    permit = db.get_permit(permit_id)
    checkpoint("current_state", {
        "permit_id": permit.id,
        "status": permit.status,
        "submitted_at": permit.submitted_at,
        "type": permit.type
    })

    # Record the review decision
    checkpoint("reviewer_info", {
        "reviewer_id": reviewer["id"],
        "department": reviewer["department"],
        "authority_level": reviewer["level"]
    })

    # Apply the decision
    permit.status = decision["status"]
    permit.decision_reason = decision["reason"]
    permit.reviewed_by = reviewer["id"]
    permit.reviewed_at = now()

    if decision.get("conditions"):
        permit.conditions = decision["conditions"]

    db.save(permit)

    return {
        "permit_id": permit.id,
        "new_status": permit.status,
        "decision_reason": decision["reason"],
        "reviewed_by": reviewer["id"],
        "reviewed_at": permit.reviewed_at,
        "conditions": permit.conditions
    }
    # Y = permit with decision applied
    # XY = publicly verifiable proof of the decision`,
      }}
      useCases={[
        {
          title: "Public records integrity",
          description:
            "Every modification to public records produces a verifiable proof. Citizens can independently verify that records have not been altered, and FOIA responses can include cryptographic proof of authenticity and completeness.",
        },
        {
          title: "Legislative tracking",
          description:
            "Track every amendment, revision, and vote on legislation as a verifiable state transition. Create a tamper-evident history of the legislative process that anyone can audit, from committee markup to final passage.",
        },
        {
          title: "Permitting and licensing",
          description:
            "Every permit application, review decision, and status change becomes a verifiable record. Applicants can track the progress of their application with confidence that the history is accurate, and agencies can prove fair and consistent processing.",
        },
        {
          title: "Election integrity",
          description:
            "Voter registration changes, ballot processing, and vote tabulation can all be recorded as verifiable state transitions. While not replacing existing election security, pruv adds an independent layer of cryptographic verification.",
        },
        {
          title: "Inter-agency data sharing",
          description:
            "When data is shared between government agencies, pruv creates verifiable records of what was shared, with whom, under what authority, and what was received. Eliminate the black box of inter-agency data flows.",
        },
        {
          title: "Grant and contract management",
          description:
            "Track the complete lifecycle of grants and contracts from application to completion. Every milestone, payment, and status change is a verifiable record, making oversight and auditing straightforward.",
        },
      ]}
    />
  );
}
