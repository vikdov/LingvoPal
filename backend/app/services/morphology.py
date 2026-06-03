"""
Morphological surface-form finder.

find_surface_form(term, context) → str | None

Finds the exact token in `context` that is a morphological form of `term`.
Strategy (in order):
  1. Exact word-boundary match — language-agnostic
  2. English irregular verbs / nouns lookup table
  3. Suffix stripping — handles regular inflections in English and most Latin-script languages

Returns the matched token from the original context (preserving case), or None.
Only used at write time (import / item creation); never called per practice request.
"""

import re

_WORD_RE = re.compile(r"\b\w+\b")

# base form → irregular surface forms (all lowercase)
_IRREGULAR: dict[str, frozenset[str]] = {
    "be": frozenset({"is", "am", "are", "was", "were", "been", "being"}),
    "have": frozenset({"has", "had", "having"}),
    "do": frozenset({"does", "did", "done", "doing"}),
    "go": frozenset({"goes", "went", "gone", "going"}),
    "say": frozenset({"says", "said", "saying"}),
    "make": frozenset({"makes", "made", "making"}),
    "know": frozenset({"knows", "knew", "known", "knowing"}),
    "think": frozenset({"thinks", "thought", "thinking"}),
    "take": frozenset({"takes", "took", "taken", "taking"}),
    "see": frozenset({"sees", "saw", "seen", "seeing"}),
    "come": frozenset({"comes", "came", "coming"}),
    "get": frozenset({"gets", "got", "gotten", "getting"}),
    "give": frozenset({"gives", "gave", "given", "giving"}),
    "find": frozenset({"finds", "found", "finding"}),
    "tell": frozenset({"tells", "told", "telling"}),
    "become": frozenset({"becomes", "became", "becoming"}),
    "show": frozenset({"shows", "showed", "shown", "showing"}),
    "leave": frozenset({"leaves", "left", "leaving"}),
    "feel": frozenset({"feels", "felt", "feeling"}),
    "bring": frozenset({"brings", "brought", "bringing"}),
    "begin": frozenset({"begins", "began", "begun", "beginning"}),
    "keep": frozenset({"keeps", "kept", "keeping"}),
    "hold": frozenset({"holds", "held", "holding"}),
    "write": frozenset({"writes", "wrote", "written", "writing"}),
    "stand": frozenset({"stands", "stood", "standing"}),
    "hear": frozenset({"hears", "heard", "hearing"}),
    "let": frozenset({"lets", "letting"}),
    "mean": frozenset({"means", "meant", "meaning"}),
    "set": frozenset({"sets", "setting"}),
    "meet": frozenset({"meets", "met", "meeting"}),
    "run": frozenset({"runs", "ran", "running"}),
    "pay": frozenset({"pays", "paid", "paying"}),
    "sit": frozenset({"sits", "sat", "sitting"}),
    "speak": frozenset({"speaks", "spoke", "spoken", "speaking"}),
    "lie": frozenset({"lies", "lay", "lain", "lying"}),
    "lead": frozenset({"leads", "led", "leading"}),
    "read": frozenset({"reads", "reading"}),
    "grow": frozenset({"grows", "grew", "grown", "growing"}),
    "lose": frozenset({"loses", "lost", "losing"}),
    "fall": frozenset({"falls", "fell", "fallen", "falling"}),
    "send": frozenset({"sends", "sent", "sending"}),
    "build": frozenset({"builds", "built", "building"}),
    "understand": frozenset({"understands", "understood", "understanding"}),
    "draw": frozenset({"draws", "drew", "drawn", "drawing"}),
    "break": frozenset({"breaks", "broke", "broken", "breaking"}),
    "spend": frozenset({"spends", "spent", "spending"}),
    "cut": frozenset({"cuts", "cutting"}),
    "hit": frozenset({"hits", "hitting"}),
    "put": frozenset({"puts", "putting"}),
    "sell": frozenset({"sells", "sold", "selling"}),
    "win": frozenset({"wins", "won", "winning"}),
    "drive": frozenset({"drives", "drove", "driven", "driving"}),
    "buy": frozenset({"buys", "bought", "buying"}),
    "wear": frozenset({"wears", "wore", "worn", "wearing"}),
    "choose": frozenset({"chooses", "chose", "chosen", "choosing"}),
    "teach": frozenset({"teaches", "taught", "teaching"}),
    "throw": frozenset({"throws", "threw", "thrown", "throwing"}),
    "rise": frozenset({"rises", "rose", "risen", "rising"}),
    "fly": frozenset({"flies", "flew", "flown", "flying"}),
    "drink": frozenset({"drinks", "drank", "drunk", "drinking"}),
    "eat": frozenset({"eats", "ate", "eaten", "eating"}),
    "swim": frozenset({"swims", "swam", "swum", "swimming"}),
    "sing": frozenset({"sings", "sang", "sung", "singing"}),
    "ring": frozenset({"rings", "rang", "rung", "ringing"}),
    "ride": frozenset({"rides", "rode", "ridden", "riding"}),
    "hide": frozenset({"hides", "hid", "hidden", "hiding"}),
    "forget": frozenset({"forgets", "forgot", "forgotten", "forgetting"}),
    "sleep": frozenset({"sleeps", "slept", "sleeping"}),
    "steal": frozenset({"steals", "stole", "stolen", "stealing"}),
    "shake": frozenset({"shakes", "shook", "shaken", "shaking"}),
    "wake": frozenset({"wakes", "woke", "woken", "waking"}),
    "hang": frozenset({"hangs", "hung", "hanging"}),
    "lay": frozenset({"lays", "laid", "laying"}),
    "child": frozenset({"children"}),
    "person": frozenset({"people"}),
    "man": frozenset({"men"}),
    "woman": frozenset({"women"}),
    "tooth": frozenset({"teeth"}),
    "foot": frozenset({"feet"}),
    "mouse": frozenset({"mice"}),
    "goose": frozenset({"geese"}),
    "ox": frozenset({"oxen"}),
}


def _candidate_bases(word: str) -> set[str]:
    """
    Generate possible base forms for a surface word via suffix stripping.
    Returns a set of lowercase candidates (including the word itself).
    """
    w = word.lower()
    result: set[str] = {w}

    # Consonant-doubling before simple suffix rules (running→run before run)
    if w.endswith("ing") and len(w) > 5:
        stem = w[:-3]
        if len(stem) >= 2 and stem[-1] == stem[-2] and stem[-1] not in "aeiou":
            result.add(stem[:-1])  # running → run
        result.add(stem)  # playing → play
        result.add(stem + "e")  # loving → love

    if w.endswith("ed") and len(w) > 4:
        stem = w[:-2]
        if len(stem) >= 2 and stem[-1] == stem[-2] and stem[-1] not in "aeiou":
            result.add(stem[:-1])  # stopped → stop
        result.add(stem)  # played → play
        result.add(stem + "e")  # loved → love

    if w.endswith("ied") and len(w) > 4:
        result.add(w[:-3] + "y")  # studied → study

    if w.endswith("ies") and len(w) > 4:
        result.add(w[:-3] + "y")  # cities → city

    if w.endswith("ves") and len(w) > 4:
        result.add(w[:-3] + "f")  # wolves → wolf

    if w.endswith("es") and len(w) > 3:
        result.add(w[:-2])  # watches → watch

    if w.endswith("s") and len(w) > 2:
        result.add(w[:-1])  # dogs → dog, plays → play

    if w.endswith("er") and len(w) > 3:
        result.add(w[:-2])  # faster → fast

    if w.endswith("est") and len(w) > 4:
        result.add(w[:-3])  # fastest → fast

    return result


def find_surface_form(term: str, context: str) -> str | None:
    """
    Find the exact token in context that is a morphological form of term.

    Returns the matched token (original case from context), or None.
    """
    if not term or not context:
        return None

    term_lower = term.lower().strip()
    irregular_forms = _IRREGULAR.get(term_lower, frozenset())

    for m in _WORD_RE.finditer(context):
        word = m.group()
        word_lower = word.lower()

        if word_lower == term_lower:
            return word

        if word_lower in irregular_forms:
            return word

        if term_lower in _candidate_bases(word_lower):
            return word

    return None


def wrap_surface_form(term: str, context: str) -> str:
    """
    Find the surface form of term in context and wrap it with {{}} markers.
    Returns context unchanged if the form is not found.

    Example: wrap_surface_form("play", "She played the piano.") → "She {{played}} the piano."
    """
    surface = find_surface_form(term, context)
    if not surface:
        return context
    return re.sub(r"\b" + re.escape(surface) + r"\b", "{{" + surface + "}}", context, count=1)


__all__ = ["find_surface_form", "wrap_surface_form"]
