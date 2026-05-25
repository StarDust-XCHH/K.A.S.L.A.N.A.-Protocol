from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from pathlib import Path

import pytest

from kaslana.core.events import CallEvent
from kaslana.core.orchestrator import Orchestrator, OrchestratorDependencies, RunOptions
from kaslana.core.states import CallState
from kaslana.ports.asr import AsrPort, Transcript
from kaslana.ports.audio import AudioChunk, AudioInputPort, AudioOutputPort
from kaslana.ports.automation import AutomationPort
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
    async def complete(
        self,
        system_prompt: str,
        turns: Sequence[ConversationTurn],
    ) -> LlmResponse:
        assert turns[-1].role == "user"
        return LlmResponse(text="早安，今天也要加油！", model="fake")


class FakeTts(TtsPort):
    async def synthesize(self, text: str) -> TtsAudio:
        return TtsAudio(audio=b"voice", sample_rate=16000, channels=1)


def build_orchestrator(
    *,
    connected: bool = True,
    vad: VadPort | None = None,
    asr: AsrPort | None = None,
) -> tuple[Orchestrator, FakeAutomation, FakeAudioInput, FakeAudioOutput]:
    automation = FakeAutomation(connected=connected)
    audio_input = FakeAudioInput()
    audio_output = FakeAudioOutput()
    orchestrator = Orchestrator(
        OrchestratorDependencies(
            automation=automation,
            audio_input=audio_input,
            audio_output=audio_output,
            vad=vad or FakeVad(),
            asr=asr or FakeAsr(),
            llm=FakeLlm(),
            tts=FakeTts(),
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
