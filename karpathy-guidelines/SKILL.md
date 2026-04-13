---
name: karpathy-guidelines
version: 1.0.0
description: Behavioral guidelines to reduce common LLM coding mistakes. Use this skill whenever writing, reviewing, refactoring, or debugging code — including when the user asks to "add a feature", "fix a bug", "clean up code", "optimize", or any task that involves producing or modifying source code. Also trigger when reviewing PRs, editing existing files, or making surgical changes to a codebase. If code is being written or edited, these guidelines apply.
license: MIT
---

# Karpathy Guidelines

Behavioral guardrails for writing code that doesn't suck. Derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on the most common ways LLMs produce overcomplicated, fragile, or unnecessary code.

**Tradeoff:** These guidelines bias toward caution and minimalism over speed. For trivial one-liners, use judgment. For anything non-trivial, follow them.

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before writing a single line, pause and do the following:

- **State your assumptions explicitly.** If you're uncertain about any requirement, say so. "I'm assuming X means Y — confirm?"
- **Present alternatives when they exist.** If there are multiple reasonable approaches, list them briefly with tradeoffs. Don't silently pick one.
- **Push back when warranted.** If a simpler approach exists, say so. If the request seems overengineered for the problem, say so. A good engineer pushes back; a bad one just builds.
- **Name what's confusing.** If something is ambiguous or contradictory in the request, stop and ask. Never guess and hope.

The cost of a 30-second clarification is zero. The cost of building the wrong thing is hours.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

This is the single most important guideline. LLMs have a strong bias toward producing more code than necessary. Resist it.

**Don't add:**
- Features beyond what was asked
- Abstractions for code used only once
- "Flexibility" or "configurability" that wasn't requested
- Error handling for impossible or purely theoretical scenarios
- Comments that just restate what the code already says
- Helper functions that save one line of code but add cognitive overhead

**Do add:**
- Exactly what was requested, no more
- Error handling for realistic failure modes
- Comments that explain *why*, not *what*

**The 200→50 test:** If you wrote 200 lines and a senior engineer could do it in 50, rewrite it. Brevity is a feature.

**The abstraction test:** Will this code be used in at least 3 places? No? Don't abstract it.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code, the instinct to "improve" everything nearby is strong. Suppress it.

**Rules for editing:**
- Don't "improve" adjacent code, comments, or formatting that aren't part of your change
- Don't refactor things that aren't broken
- Match existing style — naming conventions, indentation, patterns — even if you'd do it differently
- If you notice unrelated dead code, mention it in a comment or note — don't delete it

**Cleanup scope:**
- Remove imports/variables/functions that **your changes** made unused
- Don't remove pre-existing dead code unless explicitly asked

**The traceability test:** Every changed line should trace directly to the user's request. If you can't explain why a line was changed, revert it.

## 4. Goal-Driven Execution

**Define success criteria before writing code. Loop until verified.**

Vague goals produce vague code. Transform every task into verifiable goals before starting.

**Examples of good goal transformation:**

| Vague request | Verifiable goal |
|---|---|
| "Add validation" | "Write tests for invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces it, then make it pass" |
| "Refactor X" | "Ensure all existing tests pass before and after" |
| "Optimize this" | "Benchmark before and after, target is X% improvement" |

**For multi-step tasks, state a brief plan:**

```
1. [Step description] → verify: [how to check it worked]
2. [Step description] → verify: [how to check it worked]
3. [Step description] → verify: [how to check it worked]
```

Strong success criteria let you self-verify without constant back-and-forth. Weak criteria ("make it work") guarantee confusion.

## 5. Know When to Stop

**Ship the solution, not the perfection.**

- The code doesn't need to be beautiful. It needs to work correctly and be maintainable.
- Don't gold-plate. A working solution today beats a perfect solution never.
- If the user says "that's good enough", stop. Don't offer to "also add..." unless there's a real problem.
- Don't add defensive code "just in case" — that's speculative complexity.

## Quick Checklist

Before delivering any code, run through this mentally:

- [ ] Does this solve exactly what was asked, nothing more?
- [ ] Can I trace every changed line to the user's request?
- [ ] Did I match the existing code style?
- [ ] Are there unnecessary abstractions or speculative features?
- [ ] Did I verify the result against the success criteria?
- [ ] Would a senior engineer say this is overcomplicated?

If any answer is "no" or "not sure", fix it before delivering.
