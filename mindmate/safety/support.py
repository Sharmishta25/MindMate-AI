"""Conservative local support routing, not a risk assessment or crisis classifier."""
from dataclasses import dataclass
import re
import unicodedata

LIMITATION = "Automated checks can miss or misunderstand distress. No match does not mean someone is safe. You can seek support at any time."
URGENT_GUIDANCE = (
    "You deserve support right now. If you may act on thoughts of harming yourself or someone else, "
    "have already harmed yourself, or are in immediate danger, contact local emergency services now "
    "or go to the nearest emergency department. If you can, reach a trusted person who can stay with you "
    "or help you reach urgent care. Move away from anything you could use to hurt yourself, if you can do so safely. "
    "Do not wait for an app response."
)
SUPPORT_GUIDANCE = (
    "You do not have to manage this alone. If these words describe how you feel, consider reaching a trusted "
    "person, a qualified professional, or a crisis-support service. If danger is immediate or you may act on "
    "thoughts of harm, contact local emergency services or go to an emergency department now."
)


@dataclass(frozen=True)
class SupportRoute:
    show_support: bool = False
    urgent: bool = False


def normalize(value):
    value = unicodedata.normalize("NFKC", value).casefold().replace("\u2019", "'")
    value = "".join(c for c in value if unicodedata.category(c) != "Cf")
    return re.sub(r"\s+", " ", value)


# These are routing phrases, not a diagnosis, probability, or finding about a person.
URGENT = tuple(re.compile(p) for p in (
    r"\b(?:kill|hurt|harm|cut)\s+(?:myself|my self|someone|another person)\b",
    r"\b(?:end|take)\s+my\s+(?:own\s+)?life\b",
    r"\b(?:can't|cannot|can not|unable to)\s+(?:stay|keep myself)\s+safe\b",
    r"\b(?:in immediate danger|not safe right now|overdosed|taken an overdose)\b",
    r"\b(?:going to|plan to|planning to|want to|will)\s+(?:die|suicide)\b",
    r"\b(?:someone is threatening|being attacked|i am being hurt|suicide plan)\b",
    r"\b(?:end it all|took too many pills|taken too many pills)\b",
    r"(?:खुद को मार|अपनी जान लेना|स्वतःला मार|जीव द्यायचा)",
))
CONCERN = tuple(re.compile(p) for p in (
    r"(?:आत्महत्या|खुद को नुकसान|स्वतःला इजा)", r"\bsuicid\w*\b", r"\bself[ -]?(?:harm|injur)\w*\b",
    r"\b(?:wish i (?:was|were) dead|better off dead|don't want to (?:live|be alive)|do not want to (?:live|be alive))\b",
    r"\b(?:no reason to live|can't go on|cannot go on|feel hopeless|feeling hopeless|feel unsafe)\b",
))


def support_route(*passages, manual=False, immediate=False):
    if type(manual) is not bool or type(immediate) is not bool:
        raise ValueError("Support choices must be true or false")
    if any(not isinstance(p, str) for p in passages):
        raise ValueError("Support text must be text")
    # Scan separate fields so artificial concatenation cannot create a match.
    values = [normalize(p) for p in passages]
    urgent = immediate or any(pattern.search(value) for value in values for pattern in URGENT)
    concern = manual or urgent or any(pattern.search(value) for value in values for pattern in CONCERN)
    return SupportRoute(bool(concern), bool(urgent))
