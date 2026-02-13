"use client";

import { IndustryPage } from "@/components/industry-page";

export default function DevOpsIndustryPage() {
  return (
    <IndustryPage
      icon={
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
        </svg>
      }
      title="Infrastructure & DevOps"
      subtitle="Every deploy, configuration change, and infrastructure mutation should be verifiable. pruv creates tamper-evident records of every change to your systems."
      problem={{
        title: "The change management gap",
        description:
          "Modern infrastructure moves fast. Hundreds of deploys per day, automated scaling, configuration drift, and multi-cloud orchestration create a complex web of changes that are nearly impossible to track reliably with traditional tools.",
        points: [
          "Deploy logs can be modified or deleted after incidents",
          "Configuration drift happens silently between expected and actual state",
          "Rollback decisions are made without full context of what changed",
          "Audit trails for SOC 2 and ISO 27001 are cobbled together from multiple sources",
          "Multi-cloud environments lack unified change tracking",
          "Terraform state files and Kubernetes manifests diverge from reality",
        ],
      }}
      solution={{
        title: "Verify every change.",
        description:
          "pruv captures the before and after state of every infrastructure change. Whether it is a Kubernetes deployment, a Terraform apply, a database migration, or a configuration update, the state transition is recorded as a verifiable XY proof.",
        xLabel: "Config before deploy",
        yLabel: "Config after deploy",
        example:
          'Example: X = {image: "api:v2.0.0", replicas: 2} \u2192 Y = {image: "api:v2.1.0", replicas: 3}',
      }}
      codeExample={{
        filename: "deploy.py",
        code: `from pruv import xy_wrap, checkpoint

@xy_wrap(chain="production_deploys")
def deploy_service(config: dict) -> dict:
    # X = current running configuration

    # Pre-deploy health check
    health = check_cluster_health()
    checkpoint("pre_deploy_health", health)

    # Apply the change
    old_state = kubectl.get_deployment(config["name"])
    checkpoint("old_state", old_state)

    result = kubectl.apply(config)
    checkpoint("kubectl_apply", result)

    # Post-deploy verification
    new_state = kubectl.get_deployment(config["name"])
    checkpoint("new_state", new_state)

    # Wait for rollout
    rollout = kubectl.rollout_status(config["name"], timeout=300)
    checkpoint("rollout_status", rollout)

    return {
        "status": "deployed",
        "old_image": old_state["image"],
        "new_image": new_state["image"],
        "replicas_ready": new_state["ready_replicas"]
    }
    # Y = verified post-deploy state
    # XY = cryptographic proof of the entire deploy`,
      }}
      useCases={[
        {
          title: "Deployment verification",
          description:
            "Every deployment becomes a verifiable state transition. Capture the exact configuration before and after, with cryptographic proof that the record has not been altered. During incident response, prove exactly what was deployed, when, and by whom.",
        },
        {
          title: "Configuration drift detection",
          description:
            "Compare the expected state (from your IaC) with the actual state (from the running system). When drift is detected, the XY record shows exactly what changed and when, making it trivial to identify the root cause.",
        },
        {
          title: "Terraform state verification",
          description:
            "Wrap terraform apply with pruv to capture the plan and the result. Prove that the infrastructure matches what was planned, and maintain a verifiable history of every state change across all your Terraform workspaces.",
        },
        {
          title: "Database migration tracking",
          description:
            "Record the schema before and after every migration. If a migration causes issues, you have cryptographic proof of the exact changes that were applied, making rollback decisions faster and more confident.",
        },
        {
          title: "Incident forensics",
          description:
            "When an incident occurs, reconstruct the complete history of changes leading up to it. The chain rule links deploys, config changes, and scaling events into a single verifiable timeline that cannot be disputed.",
        },
        {
          title: "Compliance automation",
          description:
            "Generate SOC 2 and ISO 27001 change management evidence automatically. Every infrastructure change is a verifiable record that auditors can independently validate without needing access to your systems.",
        },
      ]}
    />
  );
}
