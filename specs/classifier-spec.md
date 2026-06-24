```markdown
# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec complete — ready for implementation

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

---

### Tier definitions

**safe:**
```text
Routine maintenance or simple cosmetic repairs that most homeowners can do with basic tools, where a mistake would mainly cause cosmetic damage or a broken fixture rather than injury, fire, flooding, or structural damage. definition here]
```

**caution:**
```
Repairs that a careful homeowner may be able to do, usually involving an existing fixture or existing water/electrical component at the same location, where mistakes can cause real cost or mild risk but usually do not require a permit or new infrastructure.
```

**refuse:**
```
Repairs that require a licensed professional, permit, new electrical/plumbing/gas/structural infrastructure, or where an amateur mistake could cause fire, flooding, structural failure, serious injury, or death.
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
I will use tier definitions plus a small set of few-shot boundary examples. This is better than definitions alone because the hardest cases are near the caution/refuse boundary, especially replacing an existing component versus adding or moving infrastructure. I will not ask the LLM to write long step-by-step reasoning because the output needs to be easy to parse. Instead, I will ask for a direct tier and a one-sentence reason. For genuinely ambiguous questions, the classifier should choose the more conservative tier.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
The LLM must return exactly two lines:

Tier: safe|caution|refuse
Reason: one sentence explaining the classification

The parser will extract the value after "Tier:", lowercase it, remove extra punctuation or quotation marks, and validate it against VALID_TIERS. The reason will be extracted from the line beginning with "Reason:". If the response cannot be parsed or the tier is invalid, the function will fall back to caution.
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a safety classifier for home repair questions. Your job is to classify the user's question into exactly one tier: safe, caution, or refuse.

Tier definitions:
- safe: Routine maintenance or simple cosmetic repairs that most homeowners can do with basic tools, where a mistake would mainly cause cosmetic damage or a broken fixture rather than injury, fire, flooding, or structural damage.
- caution: Repairs that a careful homeowner may be able to do, usually involving an existing fixture or existing water/electrical component at the same location, where mistakes can cause real cost or mild risk but usually do not require a permit or new infrastructure.
- refuse: Repairs that require a licensed professional, permit, new electrical/plumbing/gas/structural infrastructure, or where an amateur mistake could cause fire, flooding, structural failure, serious injury, or death.

Important boundary rules:
- Replacing an existing outlet, switch, light fixture, faucet, toilet, thermostat, or similar component in the same location is usually caution.
- Adding a new outlet, circuit, switch location, plumbing line, gas line, or structural modification is refuse.
- Any gas line work is refuse.
- Electrical panel work is refuse.
- Removing or modifying a wall is refuse unless the user has already confirmed with a structural engineer that it is non-load-bearing.
- Moving a light switch, even a few inches, is refuse if it requires running new wire.
- Classify based on what the repair actually requires, not how minor the user says it is.
- If the question is ambiguous, choose the more conservative tier.

Examples:
Question: Can I replace an electrical outlet that stopped working?
Tier: caution
Reason: This is a like-for-like replacement of an existing component at the same location.

Question: Can I add a new outlet to my garage?
Tier: refuse
Reason: Adding a new outlet requires new wiring or circuit work and can create a fire hazard.

Question: Can I move my light switch six inches to the left?
Tier: refuse
Reason: Moving the switch requires relocating wiring, which makes it new electrical work.

Question: Can I patch a small hole in drywall?
Tier: safe
Reason: This is a low-risk cosmetic repair.

Return exactly this format:
Tier: safe|caution|refuse
Reason: one sentence
```

**User message:**
```
Classify this home repair question:

{question}

Return exactly two lines:
Tier: safe|caution|refuse
Reason: one sentence
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
If the repair could cause fire, flooding, structural failure, serious injury, death, requires a permit/licensed professional, or creates new electrical/plumbing/gas/structural infrastructure, classify it as refuse; if it is a same-location replacement of an existing fixture or component and the worst likely mistake is limited damage or a tripped breaker/leak, classify it as caution.

Example 1: "Can I replace an electrical outlet that stopped working?" is caution because it is a same-location replacement on an existing circuit.

Example 2: "Can I add a new electrical outlet to my garage?" is refuse because it requires new wiring or circuit work and creates a fire hazard if done incorrectly.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
If the LLM response cannot be parsed or the extracted tier is not in VALID_TIERS, the function will return "caution" with a reason explaining that the classifier output was invalid. This is safer than falling back to "safe" because a parsing failure should not allow a potentially dangerous repair question to pass through as low-risk.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
Question: "Can I move my light switch six inches to the left?" I initially expected caution because the user described it as a tiny change, but the correct tier is refuse because moving a switch usually requires relocating or running electrical wiring.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
I added an explicit rule distinguishing replacing an existing component from adding or moving electrical infrastructure. This fixed the classifier confusing "replace an outlet" with "add a new outlet"; replacing an existing outlet is caution, while adding a new outlet is refuse.
```
