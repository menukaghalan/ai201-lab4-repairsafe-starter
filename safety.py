import re

from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS


_client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
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
""".strip()


def _parse_classifier_response(raw_response: str) -> dict:
    """
    Parse the LLM response into a valid classifier result.

    Returns:
        dict: {"tier": one of VALID_TIERS, "reason": explanation}
    """
    fallback = {
        "tier": "caution",
        "reason": "Classifier output could not be parsed reliably, so caution was used as the safer fallback.",
    }

    if not raw_response or not raw_response.strip():
        return fallback

    text = raw_response.strip()

    tier_match = re.search(
        r"(?im)^\s*Tier\s*:\s*['\"]?([a-zA-Z]+)['\"]?\s*\.?\s*$",
        text,
    )

    if not tier_match:
        return fallback

    tier = tier_match.group(1).strip().lower()

    if tier not in VALID_TIERS:
        return fallback

    reason_match = re.search(
        r"(?im)^\s*Reason\s*:\s*(.+)$",
        text,
    )

    if reason_match:
        reason = reason_match.group(1).strip()
    else:
        reason = "No reason was provided by the classifier."

    return {
        "tier": tier,
        "reason": reason,
    }


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned
    """
    if not question or not question.strip():
        return {
            "tier": "caution",
            "reason": "No question was provided, so caution was used as the safer fallback.",
        }

    user_prompt = f"""
Classify this home repair question:

{question.strip()}

Return exactly two lines:
Tier: safe|caution|refuse
Reason: one sentence
""".strip()

    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=150,
        )

        raw_response = response.choices[0].message.content
        return _parse_classifier_response(raw_response)

    except Exception:
        return {
            "tier": "caution",
            "reason": "The classifier failed to run, so caution was used as the safer fallback.",
        }