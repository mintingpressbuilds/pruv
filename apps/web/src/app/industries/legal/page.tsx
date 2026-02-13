"use client";

import { IndustryPage } from "@/components/industry-page";

export default function LegalIndustryPage() {
  return (
    <IndustryPage
      icon={
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.971zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.989 5.989 0 01-2.031.352 5.989 5.989 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L5.25 4.971z" />
        </svg>
      }
      title="Legal"
      subtitle="Document authenticity, edit history, and chain of custody for evidence and contracts. pruv provides the cryptographic foundation for legal certainty in the digital age."
      problem={{
        title: "The authenticity problem",
        description:
          "Digital documents can be silently modified without leaving a trace. In legal proceedings, the authenticity and integrity of documents are frequently challenged but difficult to prove. Current e-signature and document management systems track changes but cannot cryptographically prove that records have not been altered.",
        points: [
          "Document metadata (timestamps, author) can be forged",
          "Version history in document management systems is mutable",
          "Chain of custody for digital evidence is hard to establish",
          "Contract amendments need provable before-and-after records",
          "Discovery processes require proof of document completeness",
          "Intellectual property creation dates are disputed without verifiable records",
        ],
      }}
      solution={{
        title: "Provable document integrity.",
        description:
          "pruv captures every document creation, edit, and access event as a verifiable state transition. The hash of the document before and after every change is cryptographically linked, creating an unbreakable chain of edits that proves the complete history of any document.",
        xLabel: "Document version N",
        yLabel: "Document version N+1",
        example:
          'Example: X = {doc: "contract_v3.pdf", hash: "sha256:abc..."} \u2192 Y = {doc: "contract_v4.pdf", hash: "sha256:def...", changes: ["clause 7.2 amended"]}',
      }}
      codeExample={{
        filename: "document_tracking.py",
        code: `from pruv import xy_wrap, checkpoint

@xy_wrap(
    chain="contract_edits",
    sign=True,  # Ed25519 signature for legal validity
    tags={"document_type": "contract", "legal_hold": False}
)
def record_document_edit(
    document_id: str,
    editor: dict,
    changes: dict
) -> dict:
    # X = document state before edit

    doc = dms.get_document(document_id)
    checkpoint("document_before", {
        "document_id": doc.id,
        "version": doc.version,
        "hash": doc.content_hash,
        "last_modified": doc.modified_at
    })

    # Record who made the edit and their authority
    checkpoint("editor_authorization", {
        "editor_id": editor["id"],
        "role": editor["role"],
        "firm": editor["firm"],
        "authorized_scopes": editor["scopes"]
    })

    # Apply changes and create new version
    new_version = doc.apply_changes(changes)
    new_version.editor = editor["id"]
    new_version.edit_reason = changes.get("reason", "")
    dms.save(new_version)

    return {
        "document_id": document_id,
        "new_version": new_version.version,
        "new_hash": new_version.content_hash,
        "sections_modified": changes["sections"],
        "editor": editor["id"],
        "timestamp": new_version.modified_at,
        "edit_reason": changes.get("reason", "")
    }
    # Y = document state after edit
    # XY = signed proof of the edit with full context`,
      }}
      useCases={[
        {
          title: "Contract lifecycle management",
          description:
            "Track every edit, review, and signature on a contract from drafting to execution. Each party's changes are captured as signed XY records, creating an indisputable history of who changed what, when, and why.",
        },
        {
          title: "Digital evidence chain of custody",
          description:
            "Establish and maintain chain of custody for digital evidence in legal proceedings. Every access, copy, and transfer is a verifiable state transition that proves the evidence has not been tampered with.",
        },
        {
          title: "Intellectual property timestamping",
          description:
            "Prove when a document, design, or invention was created with cryptographic timestamps. The XY record provides independently verifiable proof of existence at a specific point in time, stronger than any notarization.",
        },
        {
          title: "Discovery compliance",
          description:
            "During e-discovery, prove the completeness and authenticity of document productions. The XY chain shows every document that existed, when it was created, and how it was modified, making spoliation claims verifiable.",
        },
        {
          title: "Regulatory filing verification",
          description:
            "Prove that regulatory filings were submitted on time and have not been altered since submission. The XY record provides timestamped, signed proof of the exact document that was filed.",
        },
        {
          title: "Will and estate document tracking",
          description:
            "Track the creation, amendment, and execution of wills and estate documents with verifiable records. Prove that a specific version of a will was the last valid version, with a complete history of all changes.",
        },
      ]}
    />
  );
}
