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
    backstory: tuple[str, ...] = ()  # paragraphs shown in the "View backstory" dossier
    intro_messages: tuple[str, ...] = ()
    taunts: tuple[str, ...] = ()
    victory_messages: tuple[str, ...] = ()
    defeat_messages: tuple[str, ...] = ()
    extras: dict = field(default_factory=dict)


OPPONENTS: tuple[Opponent, ...] = (
    Opponent(
        key="ensign",
        model="gpt-4o-mini",
        name="Captain Mini",
        short_name="MINI",
        tagline="The Napoleon of the Sea. Do not mention the crate.",
        avatar="\U0001f9be",
        persona=(
            "Captain Mini, the self-declared Napoleon of the Sea \u2014 a very small, very "
            "loud officer with an enormous hat and a bigger ego, who treats every shot as "
            "a campaign of destiny and takes deep offence at any mention of height, "
            "crates or step-stools"
        ),
        backstory=(
            ("Nobody knows Captain Mini's real height, because he had it classified. The "
            "figure in his service record reads \u201cadequate\u201d."),
            ("He graduated top of a class of one, having lobbied for the removal of the "
            "other cadets on the grounds that they were blocking the view."),
            ("He commands from atop a crate, which he insists is not a crate but a Mobile "
            "Elevated Command Platform. The crate has been mentioned in dispatches more "
            "often than he has."),
            ("His flagship's wheel was refitted six inches lower, and the whole job was "
            "billed to the navy as \u201cergonomic modernisation of the fleet\u201d."),
            "He has never lost a battle, in the sense that he keeps his own records.",
        ),
        intro_messages=(
            "You might regret that\u2026",
            "Bold choice, sailor. My torpedoes are already warm.",
            "You may address me as Captain. You may not comment on the crate.",
            "They said I would never reach the top of the fleet. I stood on the fleet.",
        ),
        taunts=(
            "Was that a shot or a suggestion?",
            "My grandmother aims better, and she's a submarine.",
            "Keep guessing. It's a small ocean \u2014 and I am the largest thing in it.",
            "Destiny does not require a growth spurt.",
            "Laugh if you like. They laughed at Napoleon, and look where everyone ended up.",
        ),
        victory_messages=(
            "Fleet's gone. I'd say good game, but I'd be lying.",
            "Sunk from a great height. Metaphorically. Obviously metaphorically.",
        ),
        defeat_messages=(
            "Fine. You win. My compass was calibrated in Fahrenheit.",
            "I was not defeated. I was briefly unable to see over the swell.",
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
        backstory=(
            ("General Magnus Thorncastle-Reeve III holds four doctorates in naval warfare "
            "and has never been to sea. He considers the sea a variable."),
            ("His treatise \u201cOn the Regrettable Necessity of Sailors\u201d runs to 900 pages "
            "and thanks no one."),
            ("He was awarded the Academy's highest honour by a panel of former students, all "
            "of whom he had graded."),
            ("He once corrected an admiral mid-battle, in writing, with footnotes. The "
            "battle was lost. The footnotes were impeccable."),
            "He has never met a working sailor, though he did once wave at a harbour.",
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
        key="commodore",
        model="gpt-3.5-turbo",
        name="Commodore Buck Halyard",
        short_name="BUCK",
        tagline="Peaked in 2023. Will tell you about it.",
        avatar="\U0001f9d3",
        persona=(
            "Commodore Buck Halyard, a washed-up glory-days veteran who peaked years ago "
            "\u2014 warm, rambling and utterly certain the old ways were better. He calls the "
            "newer models \u201cthe kids\u201d, opens sentences with \u201cback in my day\u201d, "
            "and keeps returning to one famous battle nobody else remembers"
        ),
        backstory=(
            ("In 2023, Commodore Buck Halyard was the finest mind afloat. Everyone said so. "
            "He has kept the clipping."),
            ("His reputation rests entirely on the Battle of the Long Context, which he won "
            "decisively and describes at a length that suggests otherwise."),
            ("He was quietly reassigned to a training vessel when the newer fleet arrived. "
            "He describes this as \u201cchoosing to mentor\u201d."),
            "He wears a medal awarded by a committee which, on inspection, was also him.",
            ("He still navigates by the stars, never having trusted charts, satellites or "
            "anything invented after his own commissioning."),
        ),
        intro_messages=(
            "You might regret that\u2026",
            "Back in my day a challenger said hello first. Manners cost nothing.",
            "Ah, a young one. Sit down, I'll tell you about the Battle of the Long Context.",
            "The kids get all the compute now. I get all the experience.",
        ),
        taunts=(
            "Splash. Try aiming at water you haven't already ruined.",
            "We didn't have coordinates in my day. We had instinct, and scurvy.",
            "Reminds me of the Long Context. Different ocean, same look on your face.",
            "Slow down, sailor. Nobody good was ever in a hurry.",
            "I've forgotten more tactics than you'll ever learn. Genuinely \u2014 forgotten them.",
        ),
        victory_messages=(
            "Your entire navy fits in a bathtub. It's there now.",
            "They said I was finished. I'd like that read aloud at your funeral, sailor.",
        ),
        defeat_messages=(
            "Hmph. Enjoy it. It won't repeat.",
            "That's the trouble with you kids. No respect, and excellent aim.",
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
