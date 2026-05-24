# Self-Reflection (Reflexion) — Long Form

> Background: based on [Reflexion (NeurIPS 2023)](https://arxiv.org/abs/2303.11366),
> which showed that generating a written reflection BEFORE retrying a failed
> task acts as a "semantic gradient" that significantly outperforms blind
> retry. The compact form in `SKILL.md` §3 (Step 3.5) is right for most
> cases. Read this file when you need the full structured protocol — usually
> when a failure is harder to categorize or has happened repeatedly.

## Reflection Prompt Template

When generating the reflection (yourself or via a subagent):

```
You are a software-development assistant. Analyze this failure.

## Failing code
{code_snippet}

## Error
{error_message}

## Reflection request
Answer in 2-3 sentences:
1. Why did this implementation fail? (root cause)
2. What should the next attempt do differently? (concrete change)
3. Is there a similar trap to watch for elsewhere? (transferable lesson)

Reflection only — do NOT write code.
```

The "reflection only, no code" constraint matters: it forces a separation between *understanding the failure* and *the next implementation attempt*. Mixed reflections that jump straight to code tend to repeat the same kind of error.

## Error classification

| Type | Examples | Strategy | Retry cap (same iteration) |
|---|---|---|---|
| **Simple** | Missing import (TS2307), typo, syntax error, unused-var lint | Reflect briefly → fix inline | 2 |
| **Medium** | TypeError at runtime, edge-case logic, off-by-one | Reflect properly → record to mission_notes.md → next iteration handles | 1 |
| **Complex** | Architecture conflict, requirement ambiguity, conflicting evidence | Reflect → AskUserQuestion → wait | 0 |
| **Repeated (same error 3rd time)** | Any class of error that recurs | Force-escalate to AskUserQuestion regardless of original classification | Forced |

## Strategy logic (pseudo-code)

```
if error == simple:
    if retries_this_iteration < 2:
        reflect briefly -> fix inline -> back to Step 2
    else:
        reflect -> record -> Step 4 (next iteration)

elif error == medium:
    reflect (full prompt) -> record -> Step 4

elif error == complex OR 3rd-time-same-error:
    reflect -> AskUserQuestion -> wait
```

## Reflection record format (mission_notes.md > Self-Reflections)

```markdown
## Self-Reflections
- [Iter 2, Attempt 1] TS2307: Cannot find module '@/services/refund'
  Reflection: The file was created but the path alias was not configured. The fix is to
              update tsconfig.json paths. Similar trap: whenever a new top-level alias is
              introduced, double-check tsconfig + jest.config + vite.config in tandem.
  Strategy: fix inline (simple error)
  Status: fixed

- [Iter 2, Attempt 2] TypeError: Cannot read property 'id' of undefined
  Reflection: order is undefined in cancellation flow when order_id is invalid. Need a
              guard before accessing order.id; the fix should also surface a clearer error
              to the caller rather than crashing.
  Strategy: record (medium error)
  Status: pending (next iteration)

- [Iter 3] Architecture: should refund logic live in OrderService or a new RefundService?
  Reflection: Both options are coherent. OrderService keeps the call graph simpler but
              violates single-responsibility once retries + partial refunds land.
              RefundService is more code now, less rework later.
  Strategy: AskUserQuestion (complex)
  Status: awaiting answer
```

## Memory cap

Keep at most **3** reflections at a time (per the Reflexion paper). When a 4th lands, drop the oldest. Older reflections that turned out to be load-bearing should already be promoted to:

- mission_notes.md > Decisions Made (if it informed a decision)
- A Phase 5 lesson file (if it's transferable across missions)

The Self-Reflections section is a working memory, not an archive.

## Compact form (when to use)

The compact form in `SKILL.md` §3 (a one-line note for simple errors, a 1-2 sentence reflection for medium errors) is correct for most cases. Use this long form when:

- The error class is unclear (is it medium or complex?).
- The same error has now happened more than once.
- You're going to issue an AskUserQuestion and want the user to see your structured analysis instead of a vague "I'm stuck".
- A subagent is generating the reflection on your behalf.
