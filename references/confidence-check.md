# Confidence Check — Long Form

> The compact form in `SKILL.md` §3 (High / Medium / Low + one-line reason) is
> sufficient for most iterations. The structured 4-dimension version below is
> useful in two narrow cases:
> 1. You're about to AskUserQuestion and want to show the user *which*
>    dimension is low so they can answer surgically.
> 2. You're recording the decision to `workflow_state.json` for crash recovery.

## 4 Dimensions

| Dimension | Question | Low-confidence signals (1-2) |
|---|---|---|
| **Task understanding** | Do I fully understand what's being asked? | Requirement is ambiguous; boundaries unclear; "what does 'refund' mean here?" |
| **Solution certainty** | Is the implementation approach unique? | Two equally-valid approaches; not sure which one matches project conventions |
| **Dependency clarity** | Are the APIs / modules I'll touch known? | Unsure which API to call; call order is uncertain; missing dependency information |
| **Risk estimate** | Are the side effects controllable? | Change might affect unrelated code; unsure of downstream callers |

Score each 1-5 (you don't need a rubric — your intuition is the input here). Average.

## Levels

```
🟢 High   (avg >= 4)         Proceed.
🟡 Medium (3 <= avg < 4)     Record one concern to mission_notes.md > Open Questions.
                             Pick the conservative option. Proceed.
🔴 Low    (avg < 3)          STOP. AskUserQuestion. Record answer to mission_notes.md
                             > Clarifications.
```

Boundary rule: the bands are half-open intervals — `avg = 4.0` is exactly High (proceed), `avg = 3.0` is exactly Medium. This eliminates the score-4.0 overlap that an "inclusive 3-4" reading would create.

Single-dimension override: even if the average lands in 🟢 or 🟡, **a single dimension at 1 or 2** triggers the same response as 🔴 — surface the concern, AskUserQuestion if a user decision is needed. The four typical scenarios below all show this pattern: average green, single dimension red, ask anyway. The compact form in `SKILL.md §3 Step 1.5` does NOT capture this override — that's why this file exists.

## Typical Low-confidence scenarios

When you hit one of these, structured 4-dim scoring becomes worth the overhead because it shows the user *exactly* which dimension is unsettled.

### Scenario 1 — Requirement ambiguity

```
Task: "Add a refund feature."
Task understanding: 2  (full refund only? partial? does it need approval workflow?)
Solution certainty: 4
Dependency clarity: 4
Risk estimate: 3
Average: 3.25 → 🟡, but Task understanding alone is 🔴 -> AskUserQuestion
```

### Scenario 2 — Multiple equivalent solutions

```
Task: "Add a session cache."
Task understanding: 5
Solution certainty: 2  (Map vs Object vs LRU lib — all viable)
Dependency clarity: 5
Risk estimate: 4
Average: 4.0 → 🟢, but Solution certainty alone is 🔴 -> AskUserQuestion about preference
```

### Scenario 3 — Unclear placement

```
Task: "Add a helper to parse timezone strings."
Task understanding: 5
Solution certainty: 4
Dependency clarity: 2  (does it go in services/ or utils/? what's the convention?)
Risk estimate: 5
Average: 4.0 → 🟢, but Dependency clarity alone is 🔴 -> Explore (subagent) or ask
```

### Scenario 4 — Risk is uncontrolled

```
Task: "Refactor the auth middleware."
Task understanding: 4
Solution certainty: 4
Dependency clarity: 4
Risk estimate: 1  (10+ callers; production is sensitive)
Average: 3.25 → 🟡, but Risk estimate alone is 🔴 -> Notify user before proceeding
```

The rule of thumb: **average is a coarse signal; a single dimension at 1-2 is the real trigger** for stopping. Even if the average is green, if one dimension is red, surface it before executing.

## When the compact form is wrong

The compact form ("High — plan is explicit + file shape verified") works when you're confident enough that *which* dimension you're confident about doesn't matter. The long form is for cases where the user (or future-you reading mission_notes) needs to know *why* you stopped or *why* you proceeded — and that "why" lives in a specific dimension.
