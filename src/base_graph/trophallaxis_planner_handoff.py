"""
trophallaxis_planner_handoff.py
Trophallaxis-Aware Resource Exchange During Planning Handoffs

Part of Phase 1: Core Hardening & Full Skill Exposure (SOTA Development Plan v0.1)

Implements the `trophallaxis-planner-handoff-hook`:
- Bidirectional resource (task_tokens ↔ evidence_confidence) exchange
- Deficit-gradient + efficiency-modulated transfer policy
- Reversible, provenance-aware handoffs between planner nodes and local trophallaxis clusters
- Designed to work with planner_graph, mcp_graph, and the new skill_registry / fs_graph

This enables resource homeostasis during complex multi-scale planning while preserving
emergence and hybrid control.

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class TransferDirection(str, Enum):
    TASK_TO_EVIDENCE = "task_to_evidence"
    EVIDENCE_TO_TASK = "evidence_to_evidence"
    BALANCED = "balanced"


@dataclass
class TrophallaxisTransfer:
    """Record of a single trophallaxis resource exchange during handoff."""
    from_node: str
    to_node: str
    resource_type: str  # "task_tokens" or "evidence_confidence"
    amount: float
    efficiency: float
    reason: str
    timestamp: float = field(default_factory=lambda: __import__("time").time())


@dataclass
class HandoffContext:
    """Context for a planning handoff involving trophallaxis."""
    source_planner: str
    target_cluster: str
    task_tokens_deficit: float = 0.0
    evidence_confidence_deficit: float = 0.0
    current_emergence: float = 0.7
    priority: float = 1.0


class TrophallaxisPlannerHandoffHook:
    """
    Cross-skill hook that enables bidirectional, efficiency-modulated
    trophallaxis during hierarchical planning handoffs.
    """

    def __init__(
        self,
        efficiency_base: float = 0.85,
        min_transfer: float = 0.05,
        max_transfer: float = 0.4,
    ):
        self.efficiency_base = efficiency_base
        self.min_transfer = min_transfer
        self.max_transfer = max_transfer
        self.transfer_history: List[TrophallaxisTransfer] = []

    def compute_transfer_amount(
        self,
        deficit: float,
        available: float,
        efficiency_modifier: float = 1.0,
    ) -> float:
        """Calculate how much resource to transfer based on deficit and efficiency."""
        if deficit <= 0 or available <= 0:
            return 0.0

        raw_amount = min(deficit, available * self.max_transfer)
        adjusted = raw_amount * self.efficiency_base * efficiency_modifier
        return max(self.min_transfer, min(adjusted, self.max_transfer))

    def perform_handoff(
        self,
        context: HandoffContext,
        source_resources: Dict[str, float],
        target_resources: Dict[str, float],
    ) -> List[TrophallaxisTransfer]:
        """
        Execute a trophallaxis-aware handoff.
        Returns list of transfers performed.
        """
        transfers: List[TrophallaxisTransfer] = []

        # Task tokens flow (usually from planner to cluster or vice-versa)
        task_deficit = context.task_tokens_deficit
        if task_deficit > 0 and "task_tokens" in source_resources:
            amount = self.compute_transfer_amount(
                task_deficit,
                source_resources["task_tokens"],
                efficiency_modifier=context.priority,
            )
            if amount > 0:
                transfer = TrophallaxisTransfer(
                    from_node=context.source_planner,
                    to_node=context.target_cluster,
                    resource_type="task_tokens",
                    amount=amount,
                    efficiency=self.efficiency_base * context.priority,
                    reason="planner_to_cluster_task_support",
                )
                transfers.append(transfer)
                self.transfer_history.append(transfer)

        # Evidence confidence flow (often from local cluster back to planner)
        evidence_deficit = context.evidence_confidence_deficit
        if evidence_deficit > 0 and "evidence_confidence" in target_resources:
            amount = self.compute_transfer_amount(
                evidence_deficit,
                target_resources["evidence_confidence"],
                efficiency_modifier=context.current_emergence,
            )
            if amount > 0:
                transfer = TrophallaxisTransfer(
                    from_node=context.target_cluster,
                    to_node=context.source_planner,
                    resource_type="evidence_confidence",
                    amount=amount,
                    efficiency=self.efficiency_base * context.current_emergence,
                    reason="cluster_to_planner_evidence_boost",
                )
                transfers.append(transfer)
                self.transfer_history.append(transfer)

        return transfers

    def get_transfer_summary(self) -> Dict[str, Any]:
        """Return summary statistics of recent trophallaxis activity."""
        if not self.transfer_history:
            return {"total_transfers": 0}

        total_task = sum(t.amount for t in self.transfer_history if t.resource_type == "task_tokens")
        total_evidence = sum(t.amount for t in self.transfer_history if t.resource_type == "evidence_confidence")

        return {
            "total_transfers": len(self.transfer_history),
            "total_task_tokens_transferred": round(total_task, 3),
            "total_evidence_confidence_transferred": round(total_evidence, 3),
            "last_transfer": self.transfer_history[-1] if self.transfer_history else None,
        }


# =============================================================================
# CONVENIENCE FACTORY
# =============================================================================

def create_trophallaxis_handoff_hook(
    efficiency_base: float = 0.85,
) -> TrophallaxisPlannerHandoffHook:
    """Factory aligned with v3.2.1+ trophallaxis_primed posture."""
    return TrophallaxisPlannerHandoffHook(efficiency_base=efficiency_base)


# =============================================================================
# INTEGRATION STUB
# =============================================================================

def resource_aware_plan_handoff(
    source_planner: Any,
    target_cluster: Any,
    context: Optional[Dict[str, Any]] = None,
) -> List[TrophallaxisTransfer]:
    """
    High-level integration point for planner_graph / mcp_graph handoffs.
    Future: called automatically during mode switches and level transitions.
    """
    hook = create_trophallaxis_handoff_hook()
    ctx = HandoffContext(
        source_planner=getattr(source_planner, "id", "planner"),
        target_cluster=getattr(target_cluster, "id", "cluster"),
        task_tokens_deficit=context.get("task_deficit", 0.3) if context else 0.3,
        evidence_confidence_deficit=context.get("evidence_deficit", 0.2) if context else 0.2,
        current_emergence=context.get("emergence", 0.8) if context else 0.8,
    )

    # In real usage these would come from actual node state
    source_res = {"task_tokens": 1.0}
    target_res = {"evidence_confidence": 0.9}

    return hook.perform_handoff(ctx, source_res, target_res)


if __name__ == "__main__":
    print("trophallaxis_planner_handoff v3.2.1-dev")
    hook = create_trophallaxis_handoff_hook()
    ctx = HandoffContext(
        source_planner="planner_alpha",
        target_cluster="cluster_beta",
        task_tokens_deficit=0.35,
        evidence_confidence_deficit=0.25,
    )
    transfers = hook.perform_handoff(ctx, {"task_tokens": 1.0}, {"evidence_confidence": 0.85})
    print(f"Transfers performed: {len(transfers)}")
    print(hook.get_transfer_summary())