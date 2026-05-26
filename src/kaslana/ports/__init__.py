"""Abstract ports used by the core orchestrator."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kaslana.ports.asr import AsrPort, Transcript
    from kaslana.ports.audio import AudioChunk, AudioInputPort, AudioOutputPort
    from kaslana.ports.automation import AutomationPort
    from kaslana.ports.dialogue_cache import DialogueCachePort
    from kaslana.ports.ingestion import DataIngestionPort
    from kaslana.ports.intent_router import IntentRouterPort
    from kaslana.ports.llm import ConversationTurn, LlmPort, LlmResponse
    from kaslana.ports.tts import TtsAudio, TtsPort
    from kaslana.ports.vad import SpeechSegment, VadPort
    from kaslana.ports.weather import WeatherProviderPort


_EXPORTS = {
    "AsrPort": ("kaslana.ports.asr", "AsrPort"),
    "AudioChunk": ("kaslana.ports.audio", "AudioChunk"),
    "AudioInputPort": ("kaslana.ports.audio", "AudioInputPort"),
    "AudioOutputPort": ("kaslana.ports.audio", "AudioOutputPort"),
    "AutomationPort": ("kaslana.ports.automation", "AutomationPort"),
    "ConversationTurn": ("kaslana.ports.llm", "ConversationTurn"),
    "DataIngestionPort": ("kaslana.ports.ingestion", "DataIngestionPort"),
    "DialogueCachePort": ("kaslana.ports.dialogue_cache", "DialogueCachePort"),
    "IntentRouterPort": ("kaslana.ports.intent_router", "IntentRouterPort"),
    "LlmPort": ("kaslana.ports.llm", "LlmPort"),
    "LlmResponse": ("kaslana.ports.llm", "LlmResponse"),
    "SpeechSegment": ("kaslana.ports.vad", "SpeechSegment"),
    "Transcript": ("kaslana.ports.asr", "Transcript"),
    "TtsAudio": ("kaslana.ports.tts", "TtsAudio"),
    "TtsPort": ("kaslana.ports.tts", "TtsPort"),
    "VadPort": ("kaslana.ports.vad", "VadPort"),
    "WeatherProviderPort": ("kaslana.ports.weather", "WeatherProviderPort"),
}

__all__ = [
    "AsrPort",
    "AudioChunk",
    "AudioInputPort",
    "AudioOutputPort",
    "AutomationPort",
    "ConversationTurn",
    "DataIngestionPort",
    "DialogueCachePort",
    "IntentRouterPort",
    "LlmPort",
    "LlmResponse",
    "SpeechSegment",
    "Transcript",
    "TtsAudio",
    "TtsPort",
    "VadPort",
    "WeatherProviderPort",
]


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
