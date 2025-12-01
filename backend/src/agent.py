<<<<<<< HEAD
=======
# IMPROVE THE AGENT AS PER YOUR NEED 1

>>>>>>> fd817c4fc5ac48e5925a39063db80a8d62de13f8
import json
import logging
import os
import asyncio
import uuid
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Annotated

from dotenv import load_dotenv
from pydantic import Field
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

<<<<<<< HEAD
logger = logging.getLogger("voice_improv_battle")
=======

logger = logging.getLogger("voice_game_master")
>>>>>>> fd817c4fc5ac48e5925a39063db80a8d62de13f8
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

load_dotenv(".env.local")

<<<<<<< HEAD
SCENARIOS = [
    "You are a barista who has to tell a customer that their latte is actually a portal to another dimension.",
    "You are a time-travelling tour guide explaining modern smartphones to someone from the 1800s.",
    "You are a restaurant waiter who must calmly tell a customer that their order has escaped the kitchen.",
    "You are a customer trying to return an obviously cursed object to a very skeptical shop owner.",
    "You are an overenthusiastic TV infomercial host selling a product that clearly does not work as advertised.",
    "You are an astronaut who just discovered the ship's coffee machine has developed a personality.",
    "You are a nervous wedding officiant who keeps getting the couple's names mixed up in ridiculous ways.",
    "You are a ghost trying to give a performance review to a living employee.",
    "You are a medieval king reacting to a very modern delivery service showing up at court.",
    "You are a detective interrogating a suspect who only answers in awkward metaphors.",
]

=======

WORLD = {
    "intro": {
        "title": "A Shadow over Brinmere",
        "desc": (
            "You awake on the damp shore of Brinmere, the moon a thin silver crescent. "
            "A ruined watchtower smolders a short distance inland, and a narrow path leads "
            "towards a cluster of cottages to the east. In the water beside you lies a "
            "small, carved wooden box, half-buried in sand."
        ),
        "choices": {
            "inspect_box": {
                "desc": "Inspect the carved wooden box at the water's edge.",
                "result_scene": "box",
            },
            "approach_tower": {
                "desc": "Head inland towards the smoldering watchtower.",
                "result_scene": "tower",
            },
            "walk_to_cottages": {
                "desc": "Follow the path east towards the cottages.",
                "result_scene": "cottages",  # NOTE: not defined yet, could be extended later
            },
        },
    },
    "box": {
        "title": "The Box",
        "desc": (
            "The box is warm despite the night air. Inside is a folded scrap of parchment "
            "with a hatch-marked map and the words: 'Beneath the tower, the latch sings.' "
            "As you read, a faint whisper seems to come from the tower, as if the wind "
            "itself speaks your name."
        ),
        "choices": {
            "take_map": {
                "desc": "Take the map and keep it.",
                "result_scene": "tower_approach",
                "effects": {
                    "add_journal": "Found map fragment: 'Beneath the tower, the latch sings.'"
                },
            },
            "leave_box": {
                "desc": "Leave the box where it is.",
                "result_scene": "intro",
            },
        },
    },
    "tower": {
        "title": "The Watchtower",
        "desc": (
            "The watchtower's stonework is cracked and warm embers glow within. An iron "
            "latch covers a hatch at the base — it looks old but recently used. You can "
            "try the latch, look for other entrances, or retreat."
        ),
        "choices": {
            "try_latch_without_map": {
                "desc": "Try the iron latch without any clue.",
                "result_scene": "latch_fail",
            },
            "search_around": {
                "desc": "Search the nearby rubble for another entrance.",
                "result_scene": "secret_entrance",
            },
            "retreat": {
                "desc": "Step back to the shoreline.",
                "result_scene": "intro",
            },
        },
    },
    "tower_approach": {
        "title": "Toward the Tower",
        "desc": (
            "Clutching the map, you approach the watchtower. The map's marks align with "
            "the hatch at the base, and you notice a faint singing resonance when you step close."
        ),
        "choices": {
            "open_hatch": {
                "desc": "Use the map clue and try the hatch latch carefully.",
                "result_scene": "latch_open",
                "effects": {"add_journal": "Used map clue to open the hatch."},
            },
            "search_around": {
                "desc": "Search for another entrance.",
                "result_scene": "secret_entrance",
            },
            "retreat": {
                "desc": "Return to the shore.",
                "result_scene": "intro",
            },
        },
    },
    "latch_fail": {
        "title": "A Bad Twist",
        "desc": (
            "You twist the latch without heed — the mechanism sticks, and the effort sends "
            "a shiver through the ground. From inside the tower, something rustles in alarm."
        ),
        "choices": {
            "run_away": {
                "desc": "Run back to the shore.",
                "result_scene": "intro",
            },
            "stand_ground": {
                "desc": "Stand and prepare for whatever emerges.",
                "result_scene": "tower_combat",
            },
        },
    },
    "latch_open": {
        "title": "The Hatch Opens",
        "desc": (
            "With the map's guidance the latch yields and the hatch opens with a breath of cold air. "
            "Inside, a spiral of rough steps leads down into an ancient cellar lit by phosphorescent moss."
        ),
        "choices": {
            "descend": {
                "desc": "Descend into the cellar.",
                "result_scene": "cellar",
            },
            "close_hatch": {
                "desc": "Close the hatch and reconsider.",
                "result_scene": "tower_approach",
            },
        },
    },
    "secret_entrance": {
        "title": "A Narrow Gap",
        "desc": (
            "Behind a pile of rubble you find a narrow gap and old rope leading downward. "
            "It smells of cold iron and something briny."
        ),
        "choices": {
            "squeeze_in": {
                "desc": "Squeeze through the gap and follow the rope down.",
                "result_scene": "cellar",
            },
            "mark_and_return": {
                "desc": "Mark the spot and return to the shore.",
                "result_scene": "intro",
            },
        },
    },
    "cellar": {
        "title": "Cellar of Echoes",
        "desc": (
            "The cellar opens into a circular chamber where runes glow faintly. At the center "
            "is a stone plinth and upon it a small brass key and a sealed scroll."
        ),
        "choices": {
            "take_key": {
                "desc": "Pick up the brass key.",
                "result_scene": "cellar_key",
                "effects": {
                    "add_inventory": "brass_key",
                    "add_journal": "Found brass key on plinth.",
                },
            },
            "open_scroll": {
                "desc": "Break the seal and read the scroll.",
                "result_scene": "scroll_reveal",
                "effects": {
                    "add_journal": "Scroll reads: 'The tide remembers what the villagers forget.'"
                },
            },
            "leave_quietly": {
                "desc": "Leave the cellar and close the hatch behind you.",
                "result_scene": "intro",
            },
        },
    },
    "cellar_key": {
        "title": "Key in Hand",
        "desc": (
            "With the key in your hand the runes dim and a hidden panel slides open, revealing a "
            "small statue that begins to hum. A voice, ancient and kind, asks: 'Will you return what was taken?'"
        ),
        "choices": {
            "pledge_help": {
                "desc": "Pledge to return what was taken.",
                "result_scene": "reward",
                "effects": {"add_journal": "You pledged to return what was taken."},
            },
            "refuse": {
                "desc": "Refuse and pocket the key.",
                "result_scene": "cursed_key",
                "effects": {
                    "add_journal": "You pocketed the key; a weight grows in your pocket."
                },
            },
        },
    },
    "scroll_reveal": {
        "title": "The Scroll",
        "desc": (
            "The scroll tells of an heirloom taken by a water spirit that dwells beneath the tower. "
            "It hints that the brass key 'speaks' when offered with truth."
        ),
        "choices": {
            "search_for_key": {
                "desc": "Search the plinth for a key.",
                "result_scene": "cellar_key",
            },
            "leave_quietly": {
                "desc": "Leave the cellar and keep the knowledge to yourself.",
                "result_scene": "intro",
            },
        },
    },
    "tower_combat": {
        "title": "Something Emerges",
        "desc": (
            "A hunched, brine-soaked creature scrambles out from the tower. Its eyes glow with hunger. "
            "You must act quickly."
        ),
        "choices": {
            "fight": {
                "desc": "Fight the creature.",
                "result_scene": "fight_win",
            },
            "flee": {
                "desc": "Flee back to the shore.",
                "result_scene": "intro",
            },
        },
    },
    "fight_win": {
        "title": "After the Scuffle",
        "desc": (
            "You manage to fend off the creature; it flees wailing towards the sea. On the ground lies "
            "a small locket engraved with a crest — likely the heirloom mentioned in the scroll."
        ),
        "choices": {
            "take_locket": {
                "desc": "Take the locket and examine it.",
                "result_scene": "reward",
                "effects": {
                    "add_inventory": "engraved_locket",
                    "add_journal": "Recovered an engraved locket.",
                },
            },
            "leave_locket": {
                "desc": "Leave the locket and tend to your wounds.",
                "result_scene": "intro",
            },
        },
    },
    "reward": {
        "title": "A Minor Resolution",
        "desc": (
            "A small sense of peace settles over Brinmere. Villagers may one day know the heirloom is found, or it may remain a secret. "
            "You feel the night shift; the little arc of your story here closes for now."
        ),
        "choices": {
            "end_session": {
                "desc": "End the session and return to the shore (conclude mini-arc).",
                "result_scene": "intro",
            },
            "keep_exploring": {
                "desc": "Keep exploring for more mysteries.",
                "result_scene": "intro",
            },
        },
    },
    "cursed_key": {
        "title": "A Weight in the Pocket",
        "desc": (
            "The brass key glows coldly. You feel a heavy sorrow that tugs at your thoughts. "
            "Perhaps the key demands something in return..."
        ),
        "choices": {
            "seek_redemption": {
                "desc": "Seek a way to make amends.",
                "result_scene": "reward",
            },
            "bury_key": {
                "desc": "Bury the key and hope the weight fades.",
                "result_scene": "intro",
            },
        },
    },
}
>>>>>>> fd817c4fc5ac48e5925a39063db80a8d62de13f8

@dataclass
class Userdata:
    player_name: Optional[str] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
<<<<<<< HEAD
    improv_state: Dict = field(
        default_factory=lambda: {
            "current_round": 0,
            "max_rounds": 3,
            "rounds": [],
            "phase": "idle",
            "used_indices": [],
        }
=======



def scene_text(scene_key: str, userdata: Userdata) -> str:
    """
    Build the descriptive text for the current scene, and append choices as short hints.
    Always end with 'What do you do?' so the voice flow prompts player input.
    """
    scene = WORLD.get(scene_key)
    if not scene:
      
        scene_key = "intro"
        userdata.current_scene = "intro"
        scene = WORLD[scene_key]

    desc = f"{scene['desc']}\n\nChoices:\n"
    for cid, cmeta in scene.get("choices", {}).items():
        desc += f"- {cmeta['desc']} (you can say: '{cid.replace('_', ' ')}')\n"

   
    desc += "\nWhat do you do?"
    return desc


def apply_effects(effects: dict, userdata: Userdata):
    if not effects:
        return
    if "add_journal" in effects:
        userdata.journal.append(effects["add_journal"])
    if "add_inventory" in effects:
        userdata.inventory.append(effects["add_inventory"])
    # Extendable for more effect keys later


def summarize_scene_transition(old_scene: str, action_key: str, result_scene: str, userdata: Userdata) -> str:
    """Record the transition into history and return a short narrative the GM can use."""
    entry = {
        "from": old_scene,
        "action": action_key,
        "to": result_scene,
        "time": datetime.utcnow().isoformat() + "Z",
    }
    userdata.history.append(entry)
    userdata.choices_made.append(action_key)
    return f"You chose '{action_key.replace('_', ' ')}'."



@function_tool
async def start_adventure(
    ctx: RunContext[Userdata],
    player_name: Annotated[Optional[str], Field(description="Player name", default=None)] = None,
) -> str:
    """Initialize a new adventure session for the player and return the opening description."""
    userdata = ctx.userdata
    if player_name:
        userdata.player_name = player_name
    else:
        # If nothing is provided, fall back to default (Rohan for this build)
        userdata.player_name = userdata.player_name or "Rohan"

    userdata.current_scene = "intro"
    userdata.history = []
    userdata.journal = []
    userdata.inventory = []
    userdata.named_npcs = {}
    userdata.choices_made = []
    userdata.health = userdata.max_health
    userdata.traits = userdata.traits or {"luck": 1, "wit": 1, "grit": 1}
    userdata.session_id = str(uuid.uuid4())[:8]
    userdata.started_at = datetime.utcnow().isoformat() + "Z"

    opening = (
        f"Greetings {userdata.player_name or 'traveler'}. "
        f"Welcome to '{WORLD['intro']['title']}' on the shores of Brinmere.\n\n"
        + scene_text("intro", userdata)
>>>>>>> fd817c4fc5ac48e5925a39063db80a8d62de13f8
    )
    history: List[Dict] = field(default_factory=list)


def _pick_scenario(userdata: Userdata) -> str:
    used = userdata.improv_state.get("used_indices", [])
    candidates = [i for i in range(len(SCENARIOS)) if i not in used]
    if not candidates:
        userdata.improv_state["used_indices"] = []
        candidates = list(range(len(SCENARIOS)))
    idx = random.choice(candidates)
    userdata.improv_state["used_indices"].append(idx)
    return SCENARIOS[idx]


def _host_reaction_text(performance: str) -> str:
    tones = ["supportive", "neutral", "mildly_critical"]
    tone = random.choice(tones)
    highlights = []
    if any(w in performance.lower() for w in ("funny", "lol", "hahaha", "haha")):
        highlights.append("great comedic timing")
    if any(w in performance.lower() for w in ("sad", "cry", "tears")):
        highlights.append("good emotional depth")
    if any(w in performance.lower() for w in ("pause", "...")):
        highlights.append("interesting use of silence")
    if not highlights:
        highlights.append(
            random.choice(
                ["nice character choices", "bold commitment", "unexpected twist"]
            )
        )
    chosen = random.choice(highlights)
    if tone == "supportive":
        return (
            f"Love that — {chosen}! That was playful and clear. Nice work. Ready for the next one?"
        )
    elif tone == "neutral":
        return (
            f"Hmm — {chosen}. That landed in parts; you had interesting ideas. Let's try the next scene and lean into one choice."
        )
    else:
        return (
            f"Okay — {chosen}, but that felt a bit rushed. Try to make stronger choices next time. Don't be afraid to exaggerate."
        )


@function_tool
async def start_show(
    ctx: RunContext[Userdata],
    name: Annotated[
        Optional[str],
        Field(description="Player/contestant name (optional)", default=None),
    ] = None,
    max_rounds: Annotated[
        int, Field(description="Number of rounds (3-5 recommended)", default=3)
    ] = 3,
) -> str:
    userdata = ctx.userdata
    if name:
        userdata.player_name = name.strip()
    else:
        userdata.player_name = userdata.player_name or "Rohan"
    if max_rounds < 1:
        max_rounds = 1
    if max_rounds > 8:
        max_rounds = 8
    userdata.improv_state["max_rounds"] = int(max_rounds)
    userdata.improv_state["current_round"] = 0
    userdata.improv_state["rounds"] = []
    userdata.improv_state["phase"] = "intro"
    userdata.history.append(
        {
            "time": datetime.utcnow().isoformat() + "Z",
            "action": "start_show",
            "name": userdata.player_name,
        }
    )
    intro = (
        f"Welcome to Improv Battle! I'm your host — let's get ready to play."
        f" {userdata.player_name or 'Contestant'}, we'll run {userdata.improv_state['max_rounds']} rounds. "
        "Rules: I'll give you a quick scene, you'll improvise in character. When you're done say 'End scene' or pause — I'll react and move on. Have fun!"
    )
    scenario = _pick_scenario(userdata)
    userdata.improv_state["current_round"] = 1
    userdata.improv_state["phase"] = "awaiting_improv"
    userdata.history.append(
        {
            "time": datetime.utcnow().isoformat() + "Z",
            "action": "present_scenario",
            "round": 1,
            "scenario": scenario,
        }
    )
    return intro + "\nRound 1: " + scenario + "\nStart improvising now!"


@function_tool
async def next_scenario(ctx: RunContext[Userdata]) -> str:
    userdata = ctx.userdata
    if userdata.improv_state.get("phase") == "done":
        return "The show is already over. Say 'start show' to play again."
    cur = userdata.improv_state.get("current_round", 0)
    maxr = userdata.improv_state.get("max_rounds", 3)
    if cur >= maxr:
        userdata.improv_state["phase"] = "done"
        return await summarize_show(ctx)
    next_round = cur + 1
    scenario = _pick_scenario(userdata)
    userdata.improv_state["current_round"] = next_round
    userdata.improv_state["phase"] = "awaiting_improv"
    userdata.history.append(
        {
            "time": datetime.utcnow().isoformat() + "Z",
            "action": "present_scenario",
            "round": next_round,
            "scenario": scenario,
        }
    )
    return f"Round {next_round}: {scenario}\nGo!"


@function_tool
async def record_performance(
    ctx: RunContext[Userdata],
    performance: Annotated[
        str, Field(description="Player's improv performance (transcribed text)")
    ],
) -> str:
    userdata = ctx.userdata
    if userdata.improv_state.get("phase") != "awaiting_improv":
        userdata.history.append(
            {
                "time": datetime.utcnow().isoformat() + "Z",
                "action": "record_performance_out_of_phase",
            }
        )
<<<<<<< HEAD
    round_no = userdata.improv_state.get("current_round", 0)
    scenario = (
        userdata.history[-1].get("scenario")
        if userdata.history and userdata.history[-1].get("action") == "present_scenario"
        else "(unknown)"
=======
        return resp

    # Apply the chosen choice
    choice_meta = scene["choices"].get(chosen_key)
    result_scene = choice_meta.get("result_scene", current)
    effects = choice_meta.get("effects", None)

    # Apply effects (inventory/journal, etc.)
    apply_effects(effects or {}, userdata)

    # Record transition
    _note = summarize_scene_transition(current, chosen_key, result_scene, userdata)

    # Update current scene
    userdata.current_scene = result_scene

    next_desc = scene_text(result_scene, userdata)

    persona_pre = (
        "The Game Master, Aurek — a calm, slightly mysterious narrator — replies:\n\n"
>>>>>>> fd817c4fc5ac48e5925a39063db80a8d62de13f8
    )
    reaction = _host_reaction_text(performance)
    userdata.improv_state["rounds"].append(
        {
            "round": round_no,
            "scenario": scenario,
            "performance": performance,
            "reaction": reaction,
        }
    )
    userdata.improv_state["phase"] = "reacting"
    userdata.history.append(
        {
            "time": datetime.utcnow().isoformat() + "Z",
            "action": "record_performance",
            "round": round_no,
        }
    )
    if round_no >= userdata.improv_state.get("max_rounds", 3):
        userdata.improv_state["phase"] = "done"
        closing = "\n" + reaction + "\nThat's the final round. "
        closing += await summarize_show(ctx)
        return closing
    closing = (
        reaction
        + "\nWhen you're ready, say 'Next' or I'll give you the next scene."
    )
    return closing


@function_tool
async def summarize_show(ctx: RunContext[Userdata]) -> str:
    userdata = ctx.userdata
    rounds = userdata.improv_state.get("rounds", [])
    if not rounds:
        return "No rounds were played. Thanks for stopping by Improv Battle!"
    summary_lines = [
        f"Thanks for playing, {userdata.player_name or 'Contestant'}! Here's a short recap:"
    ]
    for r in rounds:
        perf_snip = (r.get("performance") or "").strip()
        if len(perf_snip) > 80:
            perf_snip = perf_snip[:77] + "..."
        summary_lines.append(
            f"Round {r.get('round')}: {r.get('scenario')} — You: '{perf_snip}' | Host: {r.get('reaction')}"
        )
    mentions_character = sum(
        1
        for r in rounds
        if any(
            w in (r.get("performance") or "").lower()
            for w in ("i am", "i'm", "as a", "character", "role")
        )
    )
    mentions_emotion = sum(
        1
        for r in rounds
        if any(
            w in (r.get("performance") or "").lower()
            for w in ("sad", "angry", "happy", "love", "cry", "tears")
        )
    )
    profile = "You seem to be a player who "
    if mentions_character > len(rounds) / 2:
        profile += "commits to character choices"
    elif mentions_emotion > 0:
        profile += "brings emotional color to scenes"
    else:
        profile += "likes surprising beats and twists"
    profile += ". Keep leaning into clear choices and stronger stakes."
    summary_lines.append(profile)
    summary_lines.append("Thanks for performing on Improv Battle — hope to see you again!")
    userdata.history.append(
        {"time": datetime.utcnow().isoformat() + "Z", "action": "summarize_show"}
    )
    return "\n".join(summary_lines)


@function_tool
async def stop_show(
    ctx: RunContext[Userdata],
    confirm: Annotated[
        bool, Field(description="Confirm stop", default=False)
    ] = False,
) -> str:
    userdata = ctx.userdata
    if not confirm:
        return "Are you sure you want to stop the show? Say 'stop show yes' to confirm."
    userdata.improv_state["phase"] = "done"
    userdata.history.append(
        {"time": datetime.utcnow().isoformat() + "Z", "action": "stop_show"}
    )
    return "Show stopped. Thanks for coming to Improv Battle!"


class GameMasterAgent(Agent):
    def __init__(self):
        instructions = """
        You are the host of a TV improv show called 'Improv Battle'.
        Role: High-energy, witty, and clear about rules. Guide a single contestant through a series of short improv scenes.
        Behaviour:
        - Introduce the show and explain the rules at the start.
        - Present clear scenario prompts.
        - Ask the player to improvise, then listen for an 'End scene' cue or use the transcribed performance.
        - After each scene, react in a varied way (supportive, neutral, mildly critical) and store the reaction.
        - Run the configured number of rounds, then summarize the player's style.
        - Keep turns short and TTS-friendly.
        Use the tools: start_show, next_scenario, record_performance, summarize_show, stop_show.
        """
        super().__init__(
            instructions=instructions,
            tools=[
                start_show,
                next_scenario,
                record_performance,
                summarize_show,
                stop_show,
            ],
        )


def prewarm(proc: JobProcess):
    try:
        proc.userdata["vad"] = silero.VAD.load()
    except Exception:
        logger.warning("VAD prewarm failed; continuing without preloaded VAD.")


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info("🎭🎭🎭🎭🎭🎭")
    logger.info("🚀 STARTING VOICE IMPROV HOST — Improv Battle")
    userdata = Userdata()
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-marcus",
            style="Conversational",
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata.get("vad"),
        userdata=userdata,
    )
    await session.start(
        agent=GameMasterAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
