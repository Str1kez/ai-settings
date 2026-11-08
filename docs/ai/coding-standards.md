# Coding Standards

Language-agnostic principles. Applies to all code. Language-specific rules live in skill `python-standards`.

## YAGNI

Do not add functionality "for the future". Build only what the current task needs. Extract abstractions when there are **three** concrete use cases, not before. Interfaces on I/O boundaries are the exception: see Dependencies and boundaries.

## Dependencies and boundaries

- A component gets its collaborators from outside: constructor arguments or the framework's DI. It keeps them as fields and never builds them itself; global mutable state and module-level singletons stay out.
- Every boundary with I/O or an external system sits behind an interface, even with a single implementation: database, HTTP clients, queues, filesystem, clock, LLM provider. The interface holds only the methods its consumer calls and is named after the consumer's need (`UserRepository`, not `PostgresClient`). The language rules pick the mechanism.
- Pure in-process logic with a single implementation uses the concrete type. It gets an interface when a second implementation appears.
- Wiring, which implementation goes where, lives in one composition root: the app factory, `main`, or the DI container.
- Data crossing a boundary has its own schema: an API returns response schemas, never persistence models.
- Domain code raises domain errors. Translation to transport errors (HTTP status, exit code) happens at the edge, never inside services.

## Risk-based verification

Classify the change before deciding whether to add tests. Risk, not the mere
presence of changed code, determines the verification budget.

### Low risk

Examples: documentation, copy, styling, static markup, configuration values,
generated files, and mechanical wiring with no new branching or data
transformation.

- Do not add tests by default.
- Run only the cheapest applicable existing check: lint, type-check, build, or
  a focused smoke check.

### Medium risk

Examples: ordinary business logic, handlers, component behaviour, parsing, and
data transformation where failure is bounded and reversible.

- Add a test only for a key observable outcome, a non-obvious branch, or a
  regression that would otherwise be hard to notice.
- Prefer one behaviour test through a public seam over tests for every helper,
  branch, or implementation detail.
- Run the closest affected test target once after the change. Run broader
  existing tests only when the changed code is shared by them.

### High risk

Examples: a reproduced bug; authentication or authorization; money, personal
data, destructive operations, migrations, concurrency, production incidents,
or a public contract used by other systems.

- A minimal regression or contract test is required and is written first.
- Test the critical behaviour through the highest practical public seam.
- Run the affected suite. Run the full suite only when shared core behaviour
  changed, before a release, or when the user explicitly asks.

### Test budget

- Do not create a test per function, private method, trivial branch, or static
  rendering detail.
- Do not duplicate coverage already provided by a higher-level test.
- Do not make reviewers rerun passing tests without a concrete doubt that the
  recorded run does not answer.
- Any applicable test or check that was run must pass before completion. If no
  new test is warranted, state which existing check or smoke path verified the
  change.

### Writing tests

- Arrange–Act–Assert, with a blank line between the sections.
- Name a test after the behaviour it checks: `user_is_locked_after_three_failed_logins`, not `lock_user`.
- Run real in-process code and real local resources where they are cheap: a temp directory, a test database. A system you don't run (a third-party API, an LLM provider) gets a fake that implements its boundary interface. Prefer an integration test over a mock-heavy unit test.

## No dead code

- Unused imports, variables, functions, files — delete them. Don't comment them out.
- "We might need it later" → git history remembers.

## No commented-out code

- If the code isn't running, it has no right to live in the file.
- Exception: a short commented-out block with an inline comment explaining WHY it's temporarily disabled and a ticket/date for removal.

## TODOs with owner

- Every `TODO` or `FIXME` in code must have either a ticket reference or a GitHub issue link.
- A bare `TODO: fix this` is a lie.

## Comments

The reader is a senior engineer. Names, types and structure say what the code does; a comment says only what the code cannot show:

- a workaround (a library bug, a platform quirk, a deliberate hack), with the reason and a ticket when it is temporary;
- non-obvious behaviour: an ordering constraint, a side effect, an invariant the types don't express, a value taken from an external spec, what each regex group captures;
- why this approach and not the obvious one.

Doc comments go on public API where the signature doesn't state the contract (what it returns, raises, changes) or where the language's tooling requires them. They describe the contract, not the implementation steps.

## Explicit > clever

- If a colleague needs to read the code twice, rewrite it.
- Magic numbers → named constants.
- Long one-liners → multi-line with intermediate variables.

## Safety

- **Never** commit secrets. Use env vars or a secrets manager. Add sensitive file patterns to `.gitignore` proactively.
- On any path that takes user input: check for the OWASP top-10 risks for the relevant context (SQL injection, XSS, SSRF, path traversal, etc.).
- Validate at the boundary. Trust nothing from outside the process.

## Small changes

- One commit = one logical change. Don't pack refactoring, bug fix, and feature into a single commit.
- If your diff is >500 lines, pause — can it be split?
