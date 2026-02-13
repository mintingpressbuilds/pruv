"use client";

import { IndustryPage } from "@/components/industry-page";

export default function HealthcareIndustryPage() {
  return (
    <IndustryPage
      icon={
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
        </svg>
      }
      title="Healthcare"
      subtitle="Patient records, medication tracking, and clinical data require verifiable chain of custody. pruv provides HIPAA-ready cryptographic proof for every healthcare data transition."
      problem={{
        title: "The chain of custody gap",
        description:
          "Healthcare data is accessed and modified by dozens of systems and practitioners. HIPAA requires knowing who accessed what, when, and how data was changed. Current EHR systems log access events but cannot cryptographically prove that records have not been tampered with.",
        points: [
          "Patient records are modified across multiple EHR systems without unified tracking",
          "HIPAA audit trail requirements are met with fragile, mutable logs",
          "Medication administration records can be altered after the fact",
          "Lab result chains from collection to reporting lack verifiable integrity",
          "Data sharing between providers creates gaps in the audit trail",
          "Clinical trial data integrity is critical but hard to independently verify",
        ],
      }}
      solution={{
        title: "Verifiable patient record integrity.",
        description:
          "pruv captures every modification to patient data as a cryptographically signed state transition. With auto-redaction, sensitive PHI can be removed from the proof while maintaining verifiability. Every access, modification, and handoff becomes a provable event.",
        xLabel: "Record before access",
        yLabel: "Record after modification",
        example:
          'Example: X = {patient: "[REDACTED]", medication: "Metformin", dose: "500mg"} \u2192 Y = {patient: "[REDACTED]", medication: "Metformin", dose: "1000mg", modified_by: "Dr. Smith"}',
      }}
      codeExample={{
        filename: "ehr_integration.py",
        code: `from pruv import xy_wrap, checkpoint

@xy_wrap(
    chain="patient_records",
    sign=True,
    redact=["ssn", "date_of_birth", "address", "phone"],
    tags={"hipaa": True, "phi": True}
)
def update_patient_record(
    patient_id: str,
    updates: dict,
    practitioner: dict
) -> dict:
    # X = current patient record state

    record = ehr.get_patient(patient_id)
    checkpoint("current_record", record)

    # Verify practitioner authorization
    auth = verify_practitioner_access(practitioner, patient_id)
    checkpoint("authorization", {
        "practitioner_id": practitioner["id"],
        "role": practitioner["role"],
        "authorized": auth.granted,
        "scope": auth.scope
    })

    # Apply updates
    previous_values = {}
    for field, value in updates.items():
        previous_values[field] = getattr(record, field, None)
        setattr(record, field, value)

    record.last_modified_by = practitioner["id"]
    record.last_modified_at = now()
    ehr.save(record)

    return {
        "patient_id": patient_id,
        "fields_modified": list(updates.keys()),
        "previous_values": previous_values,
        "modified_by": practitioner["id"],
        "timestamp": record.last_modified_at
    }
    # Y = updated record with full change context
    # XY = HIPAA-compliant proof with PHI redacted`,
      }}
      useCases={[
        {
          title: "Patient record audit trails",
          description:
            "Every access and modification to patient records produces a verifiable proof. HIPAA auditors can independently verify that audit logs have not been tampered with, and practitioners can prove exactly what changes were made and when.",
        },
        {
          title: "Medication administration records",
          description:
            "Track the complete chain of medication events from prescription to administration. Each step (prescribed, dispensed, administered, documented) becomes a linked XY proof, creating an unbreakable chain of custody for controlled substances.",
        },
        {
          title: "Lab result chain of custody",
          description:
            "From specimen collection to result reporting, every handoff is a verifiable state transition. Prove that lab results were not modified in transit and that the chain of custody was maintained throughout the process.",
        },
        {
          title: "Clinical trial data integrity",
          description:
            "Ensure that clinical trial data meets FDA 21 CFR Part 11 requirements with cryptographic proof of data integrity. Every data point, correction, and analysis becomes a verifiable record that regulators can independently validate.",
        },
        {
          title: "Interoperability verification",
          description:
            "When patient data is exchanged between providers via FHIR or HL7, pruv creates verifiable records of what was shared, with whom, and what was received. Close the gaps in cross-system audit trails.",
        },
        {
          title: "Consent management",
          description:
            "Record every consent decision (granted, revoked, modified) as a verifiable state transition. Prove to regulators and patients that their consent preferences were respected throughout all data processing activities.",
        },
      ]}
    />
  );
}
