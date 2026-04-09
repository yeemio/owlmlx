# owlmlx Runtime Governance

> Status: authoritative
> Updated: 2026-04-09

## 1. Purpose

This document defines the governance layer for `owlmlx`.

`owlmlx` runtime governance exists to ensure that runtime truth is not limited
to architecture prose or diagnostics surfaces, but enters the actual execution
loop for risky runtime work.

## 2. Governance Scope

`owlmlx` governance covers:

- runtime risk classification
- heavy-operation execution protocol
- safe-resume rules
- boundary discipline between asset work, runtime validation, and product
  promotion
- host-safety-first decisions for runtime-risking operations

## 3. Core Governance Rules

### 3.1 Host Safety Before Runtime Ambition

For runtime-risking operations, host safety is the first constraint.

Any workflow that can materially threaten host stability, memory integrity, or
recovery posture must be governed as a runtime operation, not treated as an
ordinary asset or experiment round.

### 3.2 Execution Contract Before Heavy Expansion

Heavy operations must have an explicit execution contract before expansion.

The contract should exist before the system attempts broad execution, not after
an incident forces retroactive guardrails.

### 3.3 Runtime Truth Must Enter The Execution Loop

Memory truth, runtime truth, lifecycle truth, and path-specific limits must
become execution gates, thresholds, and stop conditions.

If these truths exist only in documents or operator commentary, governance is
incomplete.

### 3.4 Boundary Clarity Is Mandatory

Asset processing, runtime validation, and product promotion are different kinds
of work.

They may inform one another, but they must not be treated as one blended task
when the operation is heavy or host-risking.

## 4. Heavy Execution Protocol

For heavy runtime operations, `owlmlx` requires a laddered execution protocol:

1. `dry-run first`
2. `single-unit execution first`
3. `serial execution first`
4. `thresholded execution first`
5. `expansion only after prior stage passes`

This protocol is not optional for hazardous runtime work.

## 5. Safe-Resume Contract

A safe-resume contract is required when a runtime path has already crossed into
incident, crash, reboot, or host-risk territory.

At minimum, a safe-resume contract must define:

- forbidden actions
- minimum allowed resume scope
- required telemetry or memory thresholds
- abort conditions
- allowed next round shape
- honest capability reclassification

First concrete instance:
`/Users/yeemio/AI/Agent/files/verification-assets/phase-42/kimi-crash-safe-resume-gate.md`
in the Agent repo.

## 6. Product Shell Relationship

The product shell may present runtime governance outcomes, proxy governance
state, or coordinate operator actions.

It does not own runtime governance truth.

Current repository history may still refer to a product shell under older names
such as `local-llm-platform`, but those names should be treated as historical
repository labels rather than permanent runtime-truth terminology.

## 7. Governance Success Condition

`owlmlx` governance is only working when:

- runtime truth becomes execution truth
- hazardous work is classified early
- safe-resume rules exist before re-entry
- host-risking work is no longer hidden inside mixed-purpose task rounds
