---
name: host-ops
version: 1.0.0
description: |
  Use when a task runs commands on a remote host or production: ssh, deploy or provisioning scripts, a runbook, docker or systemd on a server, migrations on a live database.
  Also trigger automatically when the request names a server, a prod environment, or a deploy step that changes a machine other than this one.
  SKIP: local development, CI pipelines, docker on the user's own machine.
category: code
tags: [ops, ssh, deploy]
---

# Purpose
Every change on a remote host goes through an idempotent runner step: dry-run first, apply only after an explicit yes, executed by the `operator` agent.

# Process
Hosts and addresses live in one project table. Reference that table; never copy values into a brief.

1. Find the project runbook: the "Where to look" section of AGENTS.md, the deploy README, a project runbook skill.
   Done when: you can name the runbook file and the host table it points to. No runbook found: say so and stop.
2. Route every host change through a runner step that has a dry-run mode. No runner: propose one (contract below) before touching the host. One-off commands on the host stay unrun.
   Done when: each planned change maps to a named runner step, or a runner proposal is sent to the user.
3. Run dry-run first and compare its plan to the expected plan. Apply on production only after the user's explicit "yes" naming that host and that step. A classifier refusal is a stop: report it.
   Done when: for each step, the dry-run plan matches the expectation, and the apply carries a quoted user "yes" for that host and step.
4. Hand execution to the `operator` agent. The brief holds the ordered steps, the expected plan of each, the gates, and a link to the runbook. Stop rules live in the agent definition; the brief omits them.
   Done when: the brief lists every step with its expected plan and gates, and contains no host values copied from the table.
5. Route steps only a human can do (credentials, web consoles, interactive prompts) through the `wizard` skill.
   Done when: every human-only step is a wizard step, and no brief step asks the agent to perform one.
6. Give every step that changes the system a rollback step in the same runner (teardown, peer removal), so a manual rollback also passes through dry-run.
   Done when: each mutating step has a named rollback step with a dry-run mode.

# Reference

## Runner contract
- Steps are idempotent.
- Every mutation goes through a wrapper that prints the command in dry-run and executes it in apply.
- A file write shows its diff.
- An unknown argument exits 2.
- Every step ends with a verification.
- Payload protection refuses to ship files matched by `.gitignore`.
- The smoke test runs with a stub ssh first in PATH.

## Read-only allow rule
Narrow allow rule in the project `.claude/settings.json`: `Bash(<runner> * --dry-run)`.
Cost: the rule trusts that every step changes the system only through the wrapper. A bare mutation in a step runs during a dry-run nobody confirmed.

## Project runbook skill shape
Safety, then steps each with a "Done when", then a link to the host table.

# Output format
A short report per step: step name, dry-run plan versus expectation, apply result, verification result. Stops and refusals are reported verbatim.
