# owlmlx Runtime Contract Adoption Plan

> Status: working plan
> Updated: 2026-04-09

## 1. Purpose

This document defines how the current desktop product shell repository should
adopt `owlmlx` runtime contracts in small verified waves.

## 2. Adoption Principle

Adoption should begin with contract language, validation, and tests before
large transport or serving rewrites.

The point is to make shell-hosted runtime truth speak `owlmlx` semantics first,
then move deeper implementation over time.

## 3. Wave Plan

### Wave 1: Test-Level Adoption

Goal:

- make shell-side runtime samples pass through `owlmlx` validation

Acceptance:

- at least one shell-side test imports `owlmlx`
- core runtime sample validates against `validate_runtime_status`
- large-weight path sample validates against `validate_runtime_status`

### Wave 2: Protocol Reference Adoption

Goal:

- make shell protocol docs reference `owlmlx` contracts explicitly

Acceptance:

- shell protocol sections point to `runtime-contracts.md`
- shell protocol sections point to `runtime-status-schema.md`

### Wave 3: Transport-Layer Adoption

Goal:

- align shell response builders with `owlmlx` field language

Acceptance:

- response-building code uses terminology compatible with `owlmlx`
- contract tests assert `owlmlx`-aligned semantics

### Wave 4: Runtime-Owned Module Expansion

Goal:

- expand from schema validation into runtime-owned helper modules

Acceptance:

- `owlmlx` owns more than one executable module
- shell repo imports at least one additional runtime-owned helper

## 4. Current Round

The current round is Wave 1.

That means the minimum honest outcome is not "everything migrated", but:

- the shell repo starts importing `owlmlx`
- the first bridge validation exists
- drift is reduced at test level

Current status:

- Wave 1 complete on 2026-04-09
- Wave 2 complete on 2026-04-09
- Wave 3 complete on 2026-04-09
- Wave 4 not started
