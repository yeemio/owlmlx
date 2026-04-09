# owlmlx Rename Strategy

> Status: working strategy
> Updated: 2026-04-09

## 1. Purpose

This document defines how legacy project and repository names should be handled
while `owlmlx` becomes the runtime source of truth.

## 2. Current Naming Problem

Some current repository names and document labels were created before the
runtime boundary was fully clarified.

Those names are still useful as historical references, but they should not
continue to define permanent architecture terminology.

## 3. Naming Rule

`owlmlx` source-of-truth documents should prefer stable role names over legacy
repository names.

Preferred role names:

- `desktop product shell`
- `product shell repository`
- `current shell repository`
- `runtime source of truth`

Use historical repository names only when:

- a concrete file path must be referenced
- a migration note requires exact historical traceability
- a rename plan needs to explain old-to-new mapping

## 4. Immediate Documentation Rule

Inside `owlmlx` source-of-truth:

- do not treat legacy shell names as permanent architecture terms
- do not define runtime identity in relation to an old shell repo name
- prefer role-based naming first, with historical-name note only when needed

## 5. Rename Workstreams

### 5.1 Runtime Truth Workstream

Already in progress:

- `owlmlx` is the stable runtime name
- `large-weight runtime path` replaces specimen-led naming
- legacy shell names are being downgraded to historical references

### 5.2 Product Shell Workstream

Still pending:

- choose the future stable shell/product family name
- update shell-facing source-of-truth docs
- update protocol and UX labels
- update repository-facing references when appropriate

## 6. Rename Safety Rule

Do not block runtime-truth progress on product-shell renaming.

If the future shell name is still undecided, continue with role-based neutral
language rather than freezing another temporary name into the architecture.
