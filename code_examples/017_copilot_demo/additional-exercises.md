## Copilot Demo Exercises

Try out one or more of these to extend our copilot demo. Be mindful of your credits on free tier, you may want to lean on autocomplete before prompting.

1. Add a new column to `sample_sales.csv` (for example, a `discount` column with some missing values) and verify that the profiler handles it correctly without any code changes.

2. Use Copilot to add a `--column` flag to the command-line interface so users can profile a single column instead of all columns.

3. Ask Copilot to add a function that detects and flags columns where more than 20% of values are missing. Write a unit test for it.

4. Use Copilot Chat to identify any edge cases that the current `profile_column` function does not handle. Pick one and implement a fix.


## Key Principles for Working with Copilot

Copilot is most useful when you treat it as a capable collaborator who needs clear direction and whose work you always verify. The following principles apply across all four phases of this demo:

**Prompt with intent.** Vague prompts produce vague results. The more specific you are about what you want, what constraints apply, and what the output should look like, the better the suggestion.

**Read before you accept.** Accepting a suggestion without reading it is how bugs and bad patterns enter a codebase. Tab is fast. Reading is faster than debugging.

**Iterate, do not start over.** If a suggestion is almost right, ask Copilot to revise it. Describe what is wrong specifically. This is faster than writing from scratch and teaches you to articulate requirements precisely.

**Verify with real data.** Generated code should be tested against known inputs with known outputs. This is true of all code, but especially code you did not write line by line.

**You are still the engineer.** Copilot does not understand your business context, your client's data, or the downstream systems that depend on this code. Those judgments are yours.
