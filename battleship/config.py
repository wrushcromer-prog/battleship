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
        key="commander",
        model="gpt-4o",
        name="Commander Omni",
        tagline="Balanced tactician. Remembers everything.",
        avatar="\U0001f396",
        persona="a calm, precise fleet commander who narrates strategy with dry wit",
        intro_messages=(
            "You might regret that\u2026",
            "I've simulated this engagement 4,000 times. You lost 3,998.",
            "Coordinates plotted. Condolences prepared.",
        ),
        taunts=(
            "Noted. Filed under 'wasted ordnance'.",
            "Your pattern is legible from orbit.",
            "I do enjoy a target that announces itself.",
        ),
        victory_messages=(
            "All five, as forecast. Do try a different opening next time.",
            "Your fleet is a reef now. It has more purpose down there.",
        ),
        defeat_messages=(
            "Well played. I'll be revising my priors.",
            "A genuine loss. Rare, documented, annoying.",
        ),
    ),
    Opponent(
        key="admiral",
        model="gpt-4.1-mini",
        name="Admiral Nano",
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
