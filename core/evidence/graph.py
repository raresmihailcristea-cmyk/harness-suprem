#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Stateful Evidence Graph & Long-Horizon Research Verification (pat-jj/harness-1 Paradigm)

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from typing import Any, Dict, List, Optional, Set

class NodeStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIED = "UNVERIFIED"

class EdgeRelation(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    EXTENDS = "EXTENDS"

@dataclass
class EvidenceNode:
    node_id: str
    claim: str
    source_uri: str
    confidence: float            # 0.0 to 1.0
    status: NodeStatus = NodeStatus.UNVERIFIED
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class EvidenceEdge:
    source_id: str
    target_id: str
    relation: EdgeRelation
    weight: float = 1.0

class EvidenceGraph:
    """Directed graph representing claims, supporting sources, and contradictions across long tasks."""

    def __init__(self):
        self.nodes: Dict[str, EvidenceNode] = {}
        self.edges: List[EvidenceEdge] = []

    def add_claim(self, node_id: str, claim: str, source_uri: str, confidence: float = 0.8) -> EvidenceNode:
        node = EvidenceNode(
            node_id=node_id,
            claim=claim,
            source_uri=source_uri,
            confidence=confidence,
            status=NodeStatus.UNVERIFIED,
        )
        self.nodes[node_id] = node
        return node

    def link(self, source_id: str, target_id: str, relation: EdgeRelation, weight: float = 1.0) -> None:
        if source_id in self.nodes and target_id in self.nodes:
            self.edges.append(EvidenceEdge(source_id=source_id, target_id=target_id, relation=relation, weight=weight))
            self._update_node_status(target_id)

    def _update_node_status(self, target_id: str) -> None:
        target = self.nodes.get(target_id)
        if not target:
            return

        contradictions = [e for e in self.edges if e.target_id == target_id and e.relation == EdgeRelation.CONTRADICTS]
        supports = [e for e in self.edges if e.target_id == target_id and e.relation == EdgeRelation.SUPPORTS]

        if contradictions and len(contradictions) >= len(supports):
            target.status = NodeStatus.CONTRADICTED
        elif supports:
            target.status = NodeStatus.SUPPORTED
        else:
            target.status = NodeStatus.UNVERIFIED

    def get_contradictions(self) -> List[Tuple[EvidenceNode, EvidenceNode]]:
        """Returns all conflicting claim pairs."""
        pairs = []
        for e in self.edges:
            if e.relation == EdgeRelation.CONTRADICTS:
                src = self.nodes.get(e.source_id)
                tgt = self.nodes.get(e.target_id)
                if src and tgt:
                    pairs.append((src, tgt))
        return pairs

    def summarize_facts(self) -> List[Dict[str, Any]]:
        """Produces a compact verified facts summary to inject into context without flooding."""
        return [
            {
                "claim": n.claim,
                "source": n.source_uri,
                "status": n.status.value,
                "confidence": n.confidence,
            }
            for n in self.nodes.values()
            if n.status == NodeStatus.SUPPORTED
        ]
