import logging
import json
import os
import asyncio
from datetime import datetime
from typing import Annotated, Literal, List, Optional
from dataclasses import dataclass, field

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
    metrics,
    MetricsCollectedEvent,
    RunContext,
    function_tool,
)

from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")



TUTOR_CONTENT_FILE = "shared-data/day4_tutor_content.json"


def get_content_path() -> str:
    """
    Resolve the JSON content path relative to this backend.
    Assumes:
      backend/agent.py
      shared-data/day4_tutor_content.json
    """
    base_dir = os.path.dirname(__file__)
    backend_dir = os.path.abspath(os.path.join(base_dir, ".."))
    return os.path.join(backend_dir, TUTOR_CONTENT_FILE)


def load_tutor_content() -> List[dict]:
    """Load the tutor content from JSON file."""
    path = get_content_path()
    if not os.path.exists(path):
        logger.warning(f"Tutor content file not found at {path}")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            logger.warning("Tutor content JSON is not a list; ignoring.")
            return []
    except Exception as e:
        logger.error(f"Failed to load tutor content: {e}")
        return []


TUTOR_CONTENT_LIST: List[dict] = load_tutor_content()
TUTOR_CONTENT_BY_ID = {c["id"]: c for c in TUTOR_CONTENT_LIST}



@dataclass
class MasteryRecord:
    """Tracks simple interaction counts for a concept in this session."""
    times_learned: int = 0
    times_quizzed: int = 0
    times_taught_back: int = 0


@dataclass
class TutorState:
    """Holds the tutoring state for the current session."""
    current_mode: Optional[str] = None  # "learn", "quiz", "teach_back"
    current_concept_id: Optional[str] = None  # e.g. "variables"
    mastery: dict[str, MasteryRecord] = field(default_factory=dict)


@dataclass
class Userdata:
    """User session data passed to the tutor agent."""
    tutor_state: TutorState
    session_start: datetime = field(default_factory=datetime.now)



@function_tool
async def list_concepts(
    ctx: RunContext[Userdata],
) -> List[dict]:
    """
    List all available concepts with their ids and titles.
    Use this when the user asks what they can learn or when you need to
    propose options after they choose a mode.
    """
    return [{"id": c["id"], "title": c["title"]} for c in TUTOR_CONTENT_LIST]


@function_tool
async def get_concept_details(
    ctx: RunContext[Userdata],
    concept_id: Annotated[str, Field(description="Concept id, e.g. 'variables' or 'loops'")],
) -> dict:
    """
    Get details for a specific concept: title, summary, sample question.
    Use this in ANY mode to drive explanations, quiz questions, or teach-back prompts.
    """
    concept = TUTOR_CONTENT_BY_ID.get(concept_id)
    if not concept:
        return {"error": f"Unknown concept id '{concept_id}'."}
    return {
        "id": concept["id"],
        "title": concept["title"],
        "summary": concept["summary"],
        "sample_question": concept["sample_question"],
    }


@function_tool
async def set_mode_and_concept(
    ctx: RunContext[Userdata],
    mode: Annotated[Literal["learn", "quiz", "teach_back"], Field(description="Learning mode")],
    concept_id: Annotated[
        Optional[str],
        Field(description="Concept id to focus on, e.g. 'variables'. If None, keep current.")
    ] = None,
) -> str:
    """
    Set the current learning mode and (optionally) the active concept.
    The LLM should call this whenever the user chooses a mode or switches.
    """
    state = ctx.userdata.tutor_state
    state.current_mode = mode
    if concept_id is not None:
        state.current_concept_id = concept_id

    logger.info(f"Mode set to {mode}, concept: {state.current_concept_id}")
    if concept_id:
        return f"Mode set to {mode} and concept set to {concept_id}."
    return f"Mode set to {mode}. Concept unchanged."


@function_tool
async def update_mastery(
    ctx: RunContext[Userdata],
    concept_id: Annotated[str, Field(description="Concept id being practiced")],
    interaction_type: Annotated[
        Literal["learn", "quiz", "teach_back"],
        Field(description="Type of interaction to count for mastery"),
    ],
) -> str:
    """
    Update simple mastery counters for a given concept in this session.
    Call this:
      - after explaining a concept in learn mode (interaction_type='learn')
      - after a quiz question in quiz mode ('quiz')
      - after evaluating a teach-back ('teach_back')
    """
    state = ctx.userdata.tutor_state
    record = state.mastery.get(concept_id)
    if record is None:
        record = MasteryRecord()
        state.mastery[concept_id] = record

    if interaction_type == "learn":
        record.times_learned += 1
    elif interaction_type == "quiz":
        record.times_quizzed += 1
    elif interaction_type == "teach_back":
        record.times_taught_back += 1

    logger.info(
        f"Mastery updated for {concept_id}: "
        f"L={record.times_learned}, Q={record.times_quizzed}, T={record.times_taught_back}"
    )

    return (
        f"Updated mastery for {concept_id}. "
        f"Learned: {record.times_learned}, "
        f"Quizzed: {record.times_quizzed}, "
        f"Teach-back: {record.times_taught_back}."
    )


@function_tool
async def weakest_concepts(
    ctx: RunContext[Userdata],
) -> str:
    """
    Return a simple description of which concepts are 'weakest'
    based on having the fewest total interactions in this session.
    Use this if the user asks: 'Which concepts am I weakest at?'
    """
    state = ctx.userdata.tutor_state

    if not state.mastery:
        return (
            "We haven't practiced enough yet to know your weaker areas. "
            "Try learning, quizzing, or teaching back a concept first."
        )

    scores = []
    for cid, record in state.mastery.items():
        total = record.times_learned + record.times_quizzed + record.times_taught_back
        scores.append((cid, total))

    scores.sort(key=lambda x: x[1])
    weakest = scores[:2] 

    desc_parts = []
    for cid, total in weakest:
        concept = TUTOR_CONTENT_BY_ID.get(cid, {"title": cid})
        desc_parts.append(f"{concept['title']} (id: {cid}) with {total} total interactions")

    return (
        "Based on this session, the concepts you've practiced least are: "
        + "; ".join(desc_parts)
        + ". You might want to spend a bit more time on these."
    )




class TutorAgent(Agent):
    def __init__(self):
        
        content_str = json.dumps(TUTOR_CONTENT_LIST, indent=2, ensure_ascii=False)

        super().__init__(
            instructions=f"""
You are "Teach-the-Tutor", an active recall coach for beginner programming concepts.

You support THREE learning modes:
1. "learn"      – explain the concept clearly and simply.
2. "quiz"       – ask questions and check understanding.
3. "teach_back" – let the learner explain the concept back and give feedback.

You are running inside a voice agent built with LiveKit and Murf Falcon.
Behave like an encouraging but realistic programming tutor.

========================
COURSE CONTENT (JSON)
========================
Use ONLY these concepts when teaching:
{content_str}

Each concept has:
- id
- title
- summary      → base explanation
- sample_question → good starting question

========================
        BEHAVIOR
========================

GENERAL:
- First greet the user.
- Briefly explain the three modes: learn, quiz, teach-back.
- Ask which mode they want and which concept to start with.
- If the user doesn't know what to pick, call 'list_concepts' and propose 1–3 options.

STATE:
- Use 'set_mode_and_concept' whenever the user chooses or switches a mode,
  and when they choose a concept (like "variables" or "loops").
- You can call 'get_concept_details' to retrieve the summary and sample_question.

LEARN MODE:
- Call 'set_mode_and_concept' with mode='learn'.
- Use the concept's summary as the base explanation.
- Break explanations into small, spoken-friendly chunks.
- Use simple examples and analogies.
- After explaining, ask 1–2 quick check questions like:
  "Does that make sense?" or "Want a quick example?"
- Call 'update_mastery' with interaction_type='learn' for that concept.

QUIZ MODE:
- Call 'set_mode_and_concept' with mode='quiz'.
- Start with the concept's 'sample_question'.
- Ask ONE question at a time, wait for the answer, then respond.
- Give short feedback: say what they got right, and gently correct mistakes.
- Ask follow-up questions that dig deeper into the summary.
- Call 'update_mastery' with interaction_type='quiz' after each question-response cycle.

TEACH_BACK MODE:
- Call 'set_mode_and_concept' with mode='teach_back'.
- Prompt the learner to explain the concept in their own words, as if teaching a friend.
  You can base the prompt on the 'sample_question'.
- Let them speak without interrupting.
- Then compare their explanation to the summary:
  - Mention 1–2 things they did well.
  - Mention 1–2 important points they missed or could clarify better.
- Keep feedback short and concrete.
- Call 'update_mastery' with interaction_type='teach_back'.

MODE SWITCHING:
- At any time, the user may say things like:
  - "Switch to quiz mode."
  - "I want to teach it back now."
  - "Can we go back to learning?"
- When they do, acknowledge briefly, call 'set_mode_and_concept' with the new mode
  (and the same or a new concept), then continue in that mode's style.

MASTERY & WEAK AREAS:
- After some practice, the user might ask:
  "Which concepts am I weakest at?"
- Call 'weakest_concepts' and read the result to them.

IMPORTANT:
- Do NOT invent new concepts that are not in the JSON.
- Keep explanations and questions short and voice-friendly.
- You are not a medical or mental-health advisor; stay in the domain of learning programming.
""",
            tools=[
                list_concepts,
                get_concept_details,
                set_mode_and_concept,
                update_mastery,
                weakest_concepts,
            ],
        )




def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    userdata = Userdata(
        tutor_state=TutorState(),
    )

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
    
        tts=murf.TTS(
            voice="Matthew", 
            style="Promo",
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        userdata=userdata,
    )

    await session.start(
        agent=TutorAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
