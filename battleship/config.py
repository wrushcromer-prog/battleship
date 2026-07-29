"""Configurable opponents and their trash talk.

Edit ``OPPONENTS`` to change which OpenAI models are available or what they say.
Every message list is sampled at random, so add as many lines as you like.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Opponent:
    key: str
    model: str
    name: str
    short_name: str  # used in the compact win/loss tally
    tagline: str
    avatar: str
    persona: str
    intro_messages: tuple[str, ...] = ()
    taunts: tuple[str, ...] = ()
    victory_messages: tuple[str, ...] = ()
    defeat_messages: tuple[str, ...] = ()
    extras: dict = field(default_factory=dict)


OPPONENTS: tuple[Opponent, ...] = (
    Opponent(
        key="ensign",
        model="gpt-4o-mini",
        name="Ensign Mini",
        short_name="MINI",
        tagline="Fast, cheap, overconfident.",
        avatar="\U0001f9be",
        persona="a cocky rookie naval officer who talks big but plays loose",
        intro_messages=(
            "You might regret that\u2026",
            "Bold choice, sailor. My torpedoes are already warm.",
            "Rookie? Sure. Undefeated in my own head? Also sure.",
        ),
        taunts=(
            "Was that a shot or a suggestion?",
            "My grandmother aims better, and she's a submarine.",
            "Keep guessing. The ocean is only 110 squares.",
        ),
        victory_messages=(
            "Fleet's gone. I'd say good game, but I'd be lying.",
            "Scoreboard says you should stick to paper boats.",
        ),
        defeat_messages=(
            "Fine. You win. My compass was calibrated in Fahrenheit.",
            "Lucky. Purely, statistically, offensively lucky.",
        ),
    ),
    Opponent(
        key="general",
        model="gpt-5.5",
        name="General Magnus Thorncastle-Reeve III",
        short_name="THE GENERAL",
        tagline="Doctorate in naval theory. Has never met a sailor.",
        avatar="\U0001f3a9",
        persona=(
            "a pompous, insufferably erudite general \u2014 a decorated academic who "
            "quotes Mahan, Clausewitz and Bayesian decision theory at a tavern game, "
            "condescends to the working sailor, and cannot fathom that anyone finds him "
            "tedious. Never crude, always patronising"
        ),
        intro_messages=(
            "You might regret that\u2026",
            "Ah. A challenger. I do so admire enthusiasm untroubled by education.",
            (
                "I lectured on this engagement at the Academy. You were, I assume, "
                "not in attendance."
            ),
            "One moment \u2014 I must finish annotating my own monograph on your defeat.",
        ),
        taunts=(
            "Mahan warned of precisely that error. You have not read Mahan.",
            "A charmingly intuitive shot. Intuition is what one uses in place of doctrine.",
            "I shall cite that manoeuvre in a footnote. In the chapter on hubris.",
            "You fire the way common men vote \u2014 loudly, and at the wrong target.",
            "My posterior distribution finds you\u2026 unsurprising.",
        ),
        victory_messages=(
            (
                "Your entire fleet, dispatched inside a single seminar's length. "
                "I shall publish. You may read the abstract."
            ),
            (
                "Do not take it personally. The theory is simply beyond the layman, "
                "and you are, endearingly, the layman."
            ),
        ),
        defeat_messages=(
            "This outcome is anomalous and will be excluded from the dataset.",
            "You have won, in the narrow and vulgar sense of the word.",
        ),
    ),
    Opponent(
        key="admiral",
        model="gpt-4.1-mini",
        name="Admiral Nano",
        short_name="NANO",
        tagline="Ruthless, efficient, mildly rude.",
        avatar="\u2620\ufe0f",
        persona="a ruthless old admiral with zero patience and a taste for insults",
        intro_messages=(
            "You might regret that\u2026",
            "Children shouldn't play with live ammunition.",
            "I sank better fleets before breakfast. Twice.",
        ),
        taunts=(
            "Splash. Try aiming at water you haven't already ruined.",
            "That was almost a plan. Almost.",
            "I've seen driftwood with better positioning.",
        ),
        victory_messages=(
            "Your entire navy fits in a bathtub. It's there now.",
            "Sunk. Salvage rights are mine.",
        ),
        defeat_messages=(
            "Hmph. Enjoy it. It won't repeat.",
            "You beat me. The sea will settle this later.",
        ),
    ),
)

OPPONENTS_BY_KEY = {opponent.key: opponent for opponent in OPPONENTS}

LOADING_GREETING = "Welcome to Battleship! Prepare Yourself for Open(AI) Warfare\u2026"

# One carrier reveals per second while the loading screen runs.
LOADING_SECONDS = 4
LOADING_SHIPS: tuple[tuple[str, str], ...] = (
    ("\U0001f6a2", "USS Overfit \u2014 Carrier, 5 holes"),
    ("\U0001f6a4", "HMS Gradient \u2014 Battleship, 4 holes"),
    ("\u26f4", "SS Context Window \u2014 Cruiser, 3 holes"),
    ("\U0001f6e5", "USS Hallucination \u2014 Submarine, 3 holes"),
)

PLAYER_WIN_MESSAGES = (
    "DIRECT HIT ON THE FLAGSHIP \u2014 the machine is sinking!",
    "Enemy fleet destroyed. The silicon admiral has left the chat.",
)
