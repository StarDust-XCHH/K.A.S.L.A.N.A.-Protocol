"""Async orchestrator skeleton for the call lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from kaslana.core.events import CallEvent
from kaslana.core.states import CallState
from kaslana.domain.call_session import CallSession
from kaslana.domain.conversation import ConversationContext
from kaslana.domain.offline_cache import CachedDialogueMapping
from kaslana.ports.asr import AsrPort
from kaslana.ports.audio import AudioInputPort, AudioOutputPort
from kaslana.ports.automation import AutomationPort
from kaslana.ports.dialogue_cache import DialogueCachePort
from kaslana.ports.intent_router import IntentRouterPort
from kaslana.ports.llm import LlmPort
from kaslana.ports.tts import TtsPort
from kaslana.ports.vad import VadPort


@dataclass(frozen=True)
class OrchestratorDependencies:
    automation: AutomationPort
    audio_input: AudioInputPort
    audio_output: AudioOutputPort
    vad: VadPort
    asr: AsrPort
    llm: LlmPort
    tts: TtsPort
    dialogue_cache: DialogueCachePort | None = None
    intent_router: IntentRouterPort | None = None


@dataclass(frozen=True)
class RunOptions:
    contact_alias: str
    greeting_path: Path
    system_prompt: str = ""
    wait_timeout_s: float = 60.0
    listen_timeout_s: float = 20.0
    max_turns: int = 1
    run_date: date | None = None
    offline_cache_enabled: bool = False


class Orchestrator:
    """Coordinates ports through the state machine without knowing implementations."""

    def __init__(self, dependencies: OrchestratorDependencies) -> None:
        self._deps = dependencies

    async def run_morning_call(self, options: RunOptions) -> CallSession:
        session = CallSession.create(options.contact_alias)
        conversation = ConversationContext(system_prompt=options.system_prompt)
        mapping = await self._load_offline_mapping(options)

        try:
            await self._dial(session, options)
            if session.state is CallState.HUNG_UP:
                return session

            await self._greet(session, options, mapping)
            if session.state is CallState.HUNG_UP:
                return session

            await self._deps.audio_input.start()
            await self._conversation_loop(session, conversation, options, mapping)
        except Exception as exc:
            if session.state is not CallState.HUNG_UP:
                session.apply_event(CallEvent.FAILURE, reason=str(exc))
        finally:
            await self._shutdown_ports()

        return session

    async def _dial(self, session: CallSession, options: RunOptions) -> None:
        session.apply_event(CallEvent.START_DIAL)
        await self._deps.automation.wake_device()
        await self._deps.automation.open_wechat()
        await self._deps.automation.dial_voice_call(options.contact_alias)
        session.apply_event(CallEvent.DIAL_PLACED)

        connected = await self._deps.automation.wait_for_call_connected(options.wait_timeout_s)
        if not connected:
            session.apply_event(CallEvent.TIMEOUT, reason="call connection timeout")
            return

        session.apply_event(CallEvent.CALL_CONNECTED)

    async def _greet(
        self,
        session: CallSession,
        options: RunOptions,
        mapping: CachedDialogueMapping | None,
    ) -> None:
        greeting_path = options.greeting_path
        if mapping is not None and mapping.greeting_audio_path.exists():
            greeting_path = mapping.greeting_audio_path
        await self._deps.audio_output.play_file(greeting_path)
        session.apply_event(CallEvent.GREETING_PLAYED)

    async def _conversation_loop(
        self,
        session: CallSession,
        conversation: ConversationContext,
        options: RunOptions,
        mapping: CachedDialogueMapping | None,
    ) -> None:
        for _ in range(options.max_turns):
            segment = await self._deps.vad.collect_utterance(
                self._deps.audio_input.stream_chunks(),
                timeout_s=options.listen_timeout_s,
            )
            if segment is None:
                session.apply_event(CallEvent.TIMEOUT, reason="no speech detected")
                return

            session.apply_event(CallEvent.USER_SPEECH_CAPTURED)
            transcript = await self._deps.asr.transcribe(segment)
            if not transcript.text.strip():
                session.apply_event(CallEvent.FAILURE, reason="asr returned empty text")
                return

            conversation.append_user(transcript.text)
            if await self._try_play_cached_reply(session, conversation, transcript.text, mapping):
                continue

            session.apply_event(CallEvent.CACHE_MISS)
            response = await self._deps.llm.complete(
                conversation.system_prompt,
                conversation.to_llm_turns(),
            )
            if not response.text.strip():
                session.apply_event(CallEvent.FAILURE, reason="llm returned empty text")
                return

            session.apply_event(CallEvent.REPLY_READY)
            conversation.append_assistant(response.text)
            speech = await self._deps.tts.synthesize(response.text)
            await self._deps.audio_output.play_pcm(
                speech.audio,
                sample_rate=speech.sample_rate,
                channels=speech.channels,
            )
            session.apply_event(CallEvent.SPEECH_PLAYED)

        if session.state is not CallState.HUNG_UP:
            session.end(reason="conversation turn limit reached")

    async def _load_offline_mapping(self, options: RunOptions) -> CachedDialogueMapping | None:
        if not options.offline_cache_enabled or self._deps.dialogue_cache is None:
            return None
        try:
            return await self._deps.dialogue_cache.load_mapping(options.run_date or date.today())
        except Exception:
            return None

    async def _try_play_cached_reply(
        self,
        session: CallSession,
        conversation: ConversationContext,
        transcript: str,
        mapping: CachedDialogueMapping | None,
    ) -> bool:
        if mapping is None or self._deps.intent_router is None:
            return False

        match = self._deps.intent_router.match(transcript, mapping)
        if not match.matched or match.audio_path is None or not match.audio_path.exists():
            return False

        branch = mapping.branch_by_id(match.branch_id or "")
        if branch is not None:
            conversation.append_assistant(branch.text)

        session.apply_event(CallEvent.CACHED_REPLY_READY)
        await self._deps.audio_output.play_file(match.audio_path)
        session.apply_event(CallEvent.SPEECH_PLAYED)
        return True

    async def _shutdown_ports(self) -> None:
        for operation in (
            self._deps.automation.hang_up,
            self._deps.audio_input.stop,
            self._deps.audio_output.stop,
        ):
            try:
                await operation()
            except Exception:
                pass
