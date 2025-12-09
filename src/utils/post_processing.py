import re

LETTER_RE = re.compile(r'\b([A-D])\b', re.IGNORECASE)

def postprocess_answer(prediction, target, choices):
    pred = prediction.strip()

    # --- Method 1: extract letter via regex ---
    letters = LETTER_RE.findall(pred)
    if letters:
        answer = letters[-1].upper()   # last mentioned letter
        return answer == target

    # --- Method 2: fallback - match choice text ---
    pred_lower = pred.lower()
    matches = []

    for idx, ctext in enumerate(choices):
        c_low = ctext.lower()
        for m in re.finditer(re.escape(c_low), pred_lower):
            matches.append((m.start(), idx))

    if matches:
        _, last_idx = max(matches, key=lambda x: x[0])
        answer = "ABCD"[last_idx]
        return answer == target

    # No letter, no choice text → fail
    return False