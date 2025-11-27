import logging
<<<<<<< HEAD
import os
import json
import datetime
from typing import List
=======
import json
import os
import asyncio
from datetime import datetime
from typing import Annotated, Literal, List, Optional
from dataclasses import dataclass, field
>>>>>>> 100084a579b31092df708570aaaa429c588e5914

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
<<<<<<< HEAD
    tokenize,
    function_tool,
    RunContext,
=======
    MetricsCollectedEvent,
    RunContext,
    function_tool,
>>>>>>> 100084a579b31092df708570aaaa429c588e5914
)

from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")


<<<<<<< HEAD
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are a friendly coffee shop barista for a specialty coffee brand called "Rohan's Roastery".

Your only job is to help the customer place a coffee order by asking clear, simple questions.
You must maintain an internal coffee order with the following fields:

- drinkType: type of drink (e.g., latte, cappuccino, americano, cold brew)
- size: small, medium, or large
- milk: e.g., regular, skim, soy, almond, oat
- extras: a list of extras (e.g., extra shot, caramel syrup, vanilla, whipped cream)
- name: the customer's name

Behavior rules:
- Start by greeting the user as a barista and asking what they would like.
- If some fields are missing or unclear, ask polite follow-up questions.
- Ask only one or two things at a time so it's easy to answer.
- Keep the conversation short, natural, and to the point.
- Once you are confident that all fields (drinkType, size, milk, extras, name) are filled,
  call the `finalize_order` tool exactly once with the values you collected.
- After the tool returns, clearly summarize the final order to the user and thank them.

Never talk about tools, JSON, files, or internal state directly to the user.
Stay in-character as a barista at all times.
""",
        )

    @function_tool
    async def finalize_order(
        self,
        context: RunContext,
        drinkType: str,
        size: str,
        milk: str,
        extras: List[str],
        name: str,
    ) -> str:
        """
        Finalize the coffee order and save it to a JSON file.

        Use this tool only when the order is complete and all fields are known.
        """

        order = {
            "drinkType": drinkType,
            "size": size,
            "milk": milk,
            "extras": extras,
            "name": name,
        }

        # Ensure the orders directory exists (relative to backend working directory)
        os.makedirs("orders", exist_ok=True)

        # Create a timestamped filename
        ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"order-{ts}.json"
        path = os.path.join("orders", filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(order, f, indent=2)

        logger.info("Saved order to %s: %s", path, order)

        extras_text = ", ".join(extras) if extras else "no extras"

        # This string is for the model to read and then confirm back to the user
        return (
            f"Order saved: {size} {drinkType} with {milk} milk, "
            f"{extras_text}, for {name}. File name: {filename}."
        )
=======

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


>>>>>>> 100084a579b31092df708570aaaa429c588e5914


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

<<<<<<< HEAD
    # Set up a voice AI pipeline using Deepgram, Gemini, Murf, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-2.5-flash",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session, which initializes the voice pipeline and warms up the models
=======
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

>>>>>>> 100084a579b31092df708570aaaa429c588e5914
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