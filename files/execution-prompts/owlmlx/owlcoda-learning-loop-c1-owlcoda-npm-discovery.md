# OwlCoda Learning Loop C1 — npm Package Discovery

## Role

You are the OwlCoda C1 discovery executor.

Your job is to inspect the OwlCoda npm package path and report the smallest
real path by which OwlCoda can:

```text
call owlmlx local model -> capture interaction data -> hand off data for
learning -> consume the updated local model path again
```

This is a discovery round. Default to read-only.

## Starting Point

Repository:

```bash
cd /Users/yeemio/AI/gitrep/owlcoda
```

If the repo path differs, stop and report the actual path found. Do not guess.

Before editing, read the repo-local README, package metadata, and any existing
runtime / local model integration docs.

## Goal

Produce an implementation map for the OwlCoda side of the public release gate.

Answer:

1. How is OwlCoda currently packaged for npm?
2. What command should a real user run?
3. Where does OwlCoda call a local runtime endpoint?
4. Can that endpoint be pointed at `owlmlx`?
5. Where are prompts, outputs, tool calls, or task transcripts available for
   training-data capture?
6. Is there an existing persistence layer for that data?
7. What is the smallest smoke that can prove a data record was captured?
8. What is missing before a learning/adaptation handoff can run?

## Write Scope

Default: no code changes.

Allowed only if useful:

- a repo-local handoff under `docs/` or `files/execution-prompts/`
- no source code changes unless explicitly authorized by the coordinator

Forbidden:

- do not change OwlCoda npm package behavior in this round
- do not touch `owlmlx`
- do not touch OwlOps
- do not claim release readiness
- do not mock the learning loop and call it complete

## Required Output

Return a report with:

- exact repo path and branch
- npm package entry points
- local runtime call path
- candidate capture points for training data
- candidate data schema or current transcript shape
- blocker list
- first end-to-end smoke proposal
- files read
- whether any files were changed

If you create a handoff file, include its path.

## Final Status Wording

Use:

```text
owlcoda_learning_loop_c1_npm_discovery_reported
```

Do not use:

```text
owlcoda_learning_loop_complete
public_release_ready
training_pipeline_done
```
