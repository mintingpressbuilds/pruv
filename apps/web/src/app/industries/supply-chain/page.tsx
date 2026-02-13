"use client";

import { IndustryPage } from "@/components/industry-page";

export default function SupplyChainIndustryPage() {
  return (
    <IndustryPage
      icon={
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
        </svg>
      }
      title="Supply Chain"
      subtitle="Track provenance from source to shelf. Every handoff, transformation, and quality check becomes a verifiable record that any party in the chain can independently verify."
      problem={{
        title: "The provenance problem",
        description:
          "Global supply chains involve dozens of parties, multiple jurisdictions, and complex transformations. Tracking the origin, handling, and quality of goods relies on paper records and siloed databases that are easy to falsify and impossible to independently verify.",
        points: [
          "Paper-based certificates of origin are easy to forge",
          "Cold chain breaks in food and pharmaceuticals go undetected",
          "Conflict mineral and forced labor compliance requires verified provenance",
          "Multi-party handoffs create gaps in the chain of custody",
          "Counterfeit goods enter the supply chain through falsified documentation",
          "Recall management is slow because tracing is manual and unreliable",
        ],
      }}
      solution={{
        title: "Verifiable provenance.",
        description:
          "Every handoff, transformation, and quality check in the supply chain becomes a verifiable XY record. From raw material extraction to final delivery, the complete history of a product is captured as a cryptographic chain that any party can verify.",
        xLabel: "Goods at handoff point A",
        yLabel: "Goods at handoff point B",
        example:
          'Example: X = {batch: "B-2024-001", location: "Warehouse A", temp: "2\u00b0C"} \u2192 Y = {batch: "B-2024-001", location: "Warehouse B", temp: "3\u00b0C", transit_time: "4h"}',
      }}
      codeExample={{
        filename: "supply_chain.py",
        code: `from pruv import xy_wrap, checkpoint

@xy_wrap(chain="product_lifecycle")
def record_handoff(
    shipment_id: str,
    sender: dict,
    receiver: dict,
    conditions: dict
) -> dict:
    # X = shipment state at sender

    shipment = db.get_shipment(shipment_id)
    checkpoint("sender_state", {
        "location": sender["facility"],
        "temperature": conditions.get("temperature"),
        "humidity": conditions.get("humidity"),
        "handler": sender["id"]
    })

    # Record environmental conditions during transit
    transit_log = iot.get_transit_data(shipment_id)
    checkpoint("transit_conditions", {
        "min_temp": transit_log.min_temp,
        "max_temp": transit_log.max_temp,
        "duration_hours": transit_log.duration,
        "cold_chain_intact": transit_log.max_temp <= 8.0
    })

    # Record receipt at destination
    shipment.location = receiver["facility"]
    shipment.current_handler = receiver["id"]
    shipment.handoff_count += 1
    db.save(shipment)

    return {
        "shipment_id": shipment_id,
        "received_by": receiver["id"],
        "facility": receiver["facility"],
        "condition": conditions,
        "cold_chain_intact": transit_log.max_temp <= 8.0,
        "handoff_number": shipment.handoff_count
    }
    # Y = shipment state at receiver
    # XY = verifiable proof of the handoff`,
      }}
      useCases={[
        {
          title: "Cold chain verification",
          description:
            "IoT sensors feed temperature and humidity data into pruv at every handoff point. If the cold chain is broken, the XY record provides irrefutable proof of when and where the break occurred, along with the responsible party.",
        },
        {
          title: "Certificate of origin",
          description:
            "Replace paper certificates with cryptographic proofs. Every step from raw material extraction to finished product is a linked XY record. Anyone in the supply chain can verify the complete provenance of any item.",
        },
        {
          title: "Conflict mineral compliance",
          description:
            "Track minerals from mine to manufacturer with verifiable records at every handoff. Meet Dodd-Frank Section 1502 and EU Conflict Minerals Regulation requirements with cryptographic proof of provenance.",
        },
        {
          title: "Counterfeit prevention",
          description:
            "Every legitimate product has a verifiable chain of XY records from production to point of sale. Counterfeits can be detected by the absence or invalidity of this chain, making it mathematically impossible to insert fraudulent goods.",
        },
        {
          title: "Recall management",
          description:
            "When a recall is issued, trace the affected products through the entire supply chain instantly. The XY chain shows exactly which batches went where, which customers received them, and which items are still in transit.",
        },
        {
          title: "Sustainability reporting",
          description:
            "Track carbon footprint, water usage, and labor practices at every stage of the supply chain with verifiable records. ESG reports backed by cryptographic proof instead of self-reported estimates.",
        },
      ]}
    />
  );
}
