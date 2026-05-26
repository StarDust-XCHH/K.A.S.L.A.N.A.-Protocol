from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from datetime import date
from pathlib import Path

import pytest

from kaslana.core.events import CallEvent
from kaslana.core.orchestrator import Orchestrator, OrchestratorDependencies, RunOptions
from kaslana.core.states import CallState
from kaslana.domain.offline_cache import CachedDialogueMapping, DialogueBranch, IntentMatch
from kaslana.ports.asr import AsrPort, Transcript
from kaslana.ports.audio import AudioChunk, AudioInputPort, AudioOutputPort
from kaslana.ports.automation import AutomationPort
from kaslana.ports.dialogue_cache import DialogueCachePort
from kaslana.ports.intent_router import IntentRouterPort
from kaslana.ports.llm import ConversationTurn, LlmPort, LlmResponse
from kaslana.ports.tts import TtsAudio, TtsPort
from kaslana.ports.vad import SpeechSegment, VadPort


class FakeAutomation(AutomationPort):
    def __init__(self, connected: bool = True) -> None:
        self.connected = connected
        self.calls: list[str] = []

    async def wake_device(self) -> None:
        self.calls.append("wake_device")

    async def open_wechat(self) -> None:
        self.calls.append("open_wechat")

    async def dial_voice_call(self, contact_alias: str) -> None:
        self.calls.append(f"dial:{contact_alias}")

    async def wait_for_call_connected(self, timeout_s: float) -> bool:
        self.calls.append(f"wait:{timeout_s}")
        return self.connected

    async def hang_up(self) -> None:
        self.calls.append("hang_up")


class FakeAudioInput(AudioInputPort):
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    def stream_chunks(self) -> AsyncIterator[AudioChunk]:
        async def chunks() -> AsyncIterator[AudioChunk]:
            yield AudioChunk(data=b"input", sample_rate=16000, channels=1, timestamp_s=1.0)

        return chunks()

    async def stop(self) -> None:
        self.stopped = True


class FakeAudioOutput(AudioOutputPort):
    def __init__(self) -> None:
        self.files: list[Path] = []
        self.pcm: list[bytes] = []
        self.stopped = False

    async def play_file(self, path: Path) -> None:
        self.files.append(path)

    async def play_pcm(self, audio: bytes, sample_rate: int, channels: int) -> None:
        self.pcm.append(audio)

    async def stop(self) -> None:
        self.stopped = True


class FakeVad(VadPort):
    def __init__(self, segment: SpeechSegment | None = None) -> None:
        self.segment = segment or SpeechSegment(
            audio=b"speech",
            sample_rate=16000,
            channels=1,
            start_time_s=1.0,
            end_time_s=2.0,
        )

    async def contains_speech(self, chunk: AudioChunk) -> bool:
        return True

    async def collect_utterance(
        self,
        chunks: AsyncIterator[AudioChunk],
        timeout_s: float,
    ) -> SpeechSegment | None:
        async for _ in chunks:
            return self.segment
        return None


class FakeAsr(AsrPort):
    def __init__(self, text: str = "早上好") -> None:
        self.text = text

    async def transcribe(self, segment: SpeechSegment) -> Transcript:
        return Transcript(text=self.text, language="zh", confidence=0.99)


class FakeLlm(LlmPort):
    def __init__(self) -> None:
        self.calls = 0

    async def complete(
        self,
        system_prompt: str,
        turns: Sequence[ConversationTurn],
    ) -> LlmResponse:
        self.calls += 1
        assert turns[-1].role == "user"
        return LlmResponse(text="早安，今天也要加油！", model="fake")


class FakeTts(TtsPort):
    def __init__(self) -> None:
        self.calls = 0

    async def synthesize(self, text: str) -> TtsAudio:
        self.calls += 1
        return TtsAudio(audio=b"voice", sample_rate=16000, channels=1)


class FakeDialogueCache(DialogueCachePort):
    def __init__(self, mapping: CachedDialogueMapping | None) -> None:
        self.mapping = mapping

    async def load_mapping(self, target_date: date) -> CachedDialogueMapping | None:
        return self.mapping

    async def save_mapping(self, mapping: CachedDialogueMapping) -> None:
        self.mapping = mapping


class FakeIntentRouter(IntentRouterPort):
    def __init__(self, match: IntentMatch) -> None:
        self.match_result = match

    def match(self, transcript: str, mapping: CachedDialogueMapping) -> IntentMatch:
        return self.match_result


def build_orchestrator(
    *,
    connected: bool = True,
    vad: VadPort | None = None,
    asr: AsrPort | None = None,
    llm: FakeLlm | None = None,
    tts: FakeTts | None = None,
    dialogue_cache: DialogueCachePort | None = None,
    intent_router: IntentRouterPort | None = None,
) -> tuple[Orchestrator, FakeAutomation, FakeAudioInput, FakeAudioOutput]:
    automation = FakeAutomation(connected=connected)
    audio_input = FakeAudioInput()
    audio_output = FakeAudioOutput()
    llm = llm or FakeLlm()
    tts = tts or FakeTts()
    orchestrator = Orchestrator(
        OrchestratorDependencies(
            automation=automation,
            audio_input=audio_input,
            audio_output=audio_output,
            vad=vad or FakeVad(),
            asr=asr or FakeAsr(),
            llm=llm,
            tts=tts,
            dialogue_cache=dialogue_cache,
            intent_router=intent_router,
        )
    )
    return orchestrator, automation, audio_input, audio_output


@pytest.mark.asyncio
async def test_orchestrator_runs_one_fake_turn_and_hangs_up() -> None:
    orchestrator, automation, audio_input, audio_output = build_orchestrator()

    session = await orchestrator.run_morning_call(
        RunOptions(
            contact_alias="wake-target",
            greeting_path=Path("assets/greetings/kiana_morning.wav"),
            system_prompt="You are Kiana.",
            max_turns=1,
        )
    )

    assert session.state is CallState.HUNG_UP
    assert [transition.event for transition in session.transitions] == [
        CallEvent.START_DIAL,
        CallEvent.DIAL_PLACED,
        CallEvent.CALL_CONNECTED,
        CallEvent.GREETING_PLAYED,
        CallEvent.USER_SPEECH_CAPTURED,
        CallEvent.CACHE_MISS,
        CallEvent.REPLY_READY,
        CallEvent.SPEECH_PLAYED,
        CallEvent.HANG_UP,
    ]
    assert audio_input.started is True
    assert audio_input.stopped is True
    assert audio_output.files == [Path("assets/greetings/kiana_morning.wav")]
    assert audio_output.pcm == [b"voice"]
    assert automation.calls[-1] == "hang_up"


@pytest.mark.asyncio
async def test_orchestrator_hangs_up_when_call_never_connects() -> None:
    orchestrator, _, audio_input, audio_output = build_orchestrator(connected=False)

    session = await orchestrator.run_morning_call(
        RunOptions(contact_alias="wake-target", greeting_path=Path("greeting.wav"))
    )

    assert session.state is CallState.HUNG_UP
    assert session.end_reason == "call connection timeout"
    assert [transition.event for transition in session.transitions] == [
        CallEvent.START_DIAL,
        CallEvent.DIAL_PLACED,
        CallEvent.TIMEOUT,
    ]
    assert audio_input.started is False
    assert audio_output.files == []


@pytest.mark.asyncio
async def test_orchestrator_records_failure_for_empty_asr_text() -> None:
    orchestrator, _, _, _ = build_orchestrator(asr=FakeAsr(text="   "))

    session = await orchestrator.run_morning_call(
        RunOptions(contact_alias="wake-target", greeting_path=Path("greeting.wav"))
    )

    assert session.state is CallState.HUNG_UP
    assert session.failure_reason == "asr returned empty text"
    assert session.transitions[-1].event is CallEvent.FAILURE


@pytest.mark.asyncio
async def test_orchestrator_plays_cached_greeting_and_branch(tmp_path: Path) -> None:
    cached_greeting = tmp_path / "greeting.wav"
    branch_audio = tmp_path / "complaint.wav"
    cached_greeting.write_bytes(b"wav")
    branch_audio.write_bytes(b"wav")
    mapping = CachedDialogueMapping(
        target_date=date(2026, 5, 25),
        greeting_text="缓存早安。",
        greeting_audio_path=cached_greeting,
        branches=(
            DialogueBranch(
                branch_id="complaint",
                intent="complaint",
                text="缓存反驳。",
                audio_path=branch_audio,
            ),
        ),
    )
    llm = FakeLlm()
    tts = FakeTts()
    orchestrator, _, _, audio_output = build_orchestrator(
        llm=llm,
        tts=tts,
        dialogue_cache=FakeDialogueCache(mapping),
        intent_router=FakeIntentRouter(
            IntentMatch(
                branch_id="complaint",
                confidence=1.0,
                matched=True,
                audio_path=branch_audio,
            )
        ),
    )

    session = await orchestrator.run_morning_call(
        RunOptions(
            contact_alias="wake-target",
            greeting_path=Path("fallback.wav"),
            max_turns=1,
            run_date=date(2026, 5, 25),
            offline_cache_enabled=True,
        )
    )

    assert session.state is CallState.HUNG_UP
    assert audio_output.files == [cached_greeting, branch_audio]
    assert audio_output.pcm == []
    assert llm.calls == 0
    assert tts.calls == 0
    assert CallEvent.CACHED_REPLY_READY in [transition.event for transition in session.transitions]


@pytest.mark.asyncio
async def test_orchestrator_falls_back_to_realtime_when_cache_misses(tmp_path: Path) -> None:
    cached_greeting = tmp_path / "greeting.wav"
    branch_audio = tmp_path / "complaint.wav"
    cached_greeting.write_bytes(b"wav")
    branch_audio.write_bytes(b"wav")
    mapping = CachedDialogueMapping(
        target_date=date(2026, 5, 25),
        greeting_text="缓存早安。",
        greeting_audio_path=cached_greeting,
        branches=(
            DialogueBranch(
                branch_id="complaint",
                intent="complaint",
                text="缓存反驳。",
                audio_path=branch_audio,
            ),
        ),
    )
    llm = FakeLlm()
    tts = FakeTts()
    orchestrator, _, _, audio_output = build_orchestrator(
        llm=llm,
        tts=tts,
        dialogue_cache=FakeDialogueCache(mapping),
        intent_router=FakeIntentRouter(
            IntentMatch(branch_id=None, confidence=0.0, matched=False)
        ),
    )

    session = await orchestrator.run_morning_call(
        RunOptions(
            contact_alias="wake-target",
            greeting_path=Path("fallback.wav"),
            max_turns=1,
            run_date=date(2026, 5, 25),
            offline_cache_enabled=True,
        )
    )

    assert session.state is CallState.HUNG_UP
    assert audio_output.files == [cached_greeting]
    assert audio_output.pcm == [b"voice"]
    assert llm.calls == 1
    assert tts.calls == 1
    assert CallEvent.CACHE_MISS in [transition.event for transition in session.transitions]
