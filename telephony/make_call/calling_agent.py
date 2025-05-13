import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from RIME_API_KEY=RCeQaNFgMSLAzmr6Z9gE4bt84MtPDmc941o01SdEw5Q
from from dotenv import load_dotenv
import os

load_dotenv(
    dotenv_path=Path(__file__).parent.parent.parent / ".env"
)

class JessieAgent(Agent):
    def __init__(self):
        super().__init__(…)
        self.live_agent_number = os.getenv("LIVE_AGENT_NUMBER")
    …
    async def on_transcript(…):
        …
        await self.session.handoff_to_human(to=self.live_agent_number)

logger = logging.getLogger("jessie-agent")
logger.setLevel(logging.INFO)

POSITIVE_KEYWORDS   = {"yes", "sure", "absolutely", "definitely", "yeah", "yep", "sounds good"}
RESCHEDULE_KEYWORDS = {"later", "call me", "schedule", "tomorrow", "next week"}

class JessieAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=None,  # we’ll drive via code, not a giant prompt
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )
        self.state = "INTRO"

    async def on_enter(self):
        # Fire the approved opening line
        await self.session.send_tts(
            "Hi, I’m Jessie from My A C Guy of South Florida. "
            "We’re offering a completely free A C inspection this season. "
            "Would you like to hear more?"
        )

    async def on_transcript(self, transcript: str, is_final: bool):
        if not is_final:
            return

        text = transcript.strip().lower()
        logger.info(f"[{self.state}] User said: “{text}”")

        if self.state == "INTRO":
            # Positive intent → hand off
            if any(word in text for word in POSITIVE_KEYWORDS):
                await self.session.send_tts(
                    "Fantastic! I’ll connect you to one of our specialists right now."
                )
                await self.session.handoff_to_human()  # your dialer hook
                self.state = "BOOKED"

            # Wants callback later → collect scheduling info
            elif any(word in text for word in RESCHEDULE_KEYWORDS):
                await self.session.send_tts(
                    "No problem—what day and time works best for you?"
                )
                self.state = "COLLECT_INFO"

            # Anything else → fallback to human
            else:
                await self.session.send_tts(
                    "Sorry, I didn’t catch that. Let me transfer you to a specialist."
                )
                await self.session.handoff_to_human()
                self.state = "BOOKED"

        elif self.state == "COLLECT_INFO":
            # Here you’d parse the user’s reply for date/time
            # For demo, we just echo it back and hang up
            requested_time = text  # replace with real NLP extraction
            # e.g. store callback request via your own webhook here
            logger.info(f"Scheduling callback at: {requested_time}")
            await self.session.send_tts(
                f"Great—we’ll call you on {requested_time}. Have a great day!"
            )
            await self.session.hangup()
            self.state = "SCHEDULED"

    async def on_error(self, error: Exception):
        logger.error("Unexpected error, handing off to human", exc_info=error)
        await self.session.handoff_to_human()

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession()
    await session.start(agent=JessieAgent(), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
