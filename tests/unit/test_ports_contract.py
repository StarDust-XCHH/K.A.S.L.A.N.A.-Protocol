from __future__ import annotations

from kaslana.adapters.asr import FasterWhisperAsr
from kaslana.adapters.audio import SoundDeviceAudioInput, SoundDeviceAudioOutput
from kaslana.adapters.automation import Uiautomator2WechatAutomation
from kaslana.adapters.dialogue_cache import JsonDialogueCache
from kaslana.adapters.ingestion import LocalFilesDataIngestion
from kaslana.adapters.intent_router import RegexIntentRouter
from kaslana.adapters.llm import OpenAICompatibleLlm
from kaslana.adapters.tts import GptSovitsTts
from kaslana.adapters.vad import SileroVad
from kaslana.adapters.weather import StaticWeatherProvider
from kaslana.ports.asr import AsrPort
from kaslana.ports.audio import AudioInputPort, AudioOutputPort
from kaslana.ports.automation import AutomationPort
from kaslana.ports.dialogue_cache import DialogueCachePort
from kaslana.ports.ingestion import DataIngestionPort
from kaslana.ports.intent_router import IntentRouterPort
from kaslana.ports.llm import LlmPort
from kaslana.ports.tts import TtsPort
from kaslana.ports.vad import VadPort
from kaslana.ports.weather import WeatherProviderPort


def test_placeholder_adapters_satisfy_port_interfaces() -> None:
    assert isinstance(Uiautomator2WechatAutomation(), AutomationPort)
    assert isinstance(SoundDeviceAudioInput(), AudioInputPort)
    assert isinstance(SoundDeviceAudioOutput(), AudioOutputPort)
    assert isinstance(SileroVad(), VadPort)
    assert isinstance(FasterWhisperAsr(), AsrPort)
    assert isinstance(OpenAICompatibleLlm(), LlmPort)
    assert isinstance(GptSovitsTts(), TtsPort)
    assert isinstance(JsonDialogueCache(), DialogueCachePort)
    assert isinstance(RegexIntentRouter(), IntentRouterPort)
    assert isinstance(LocalFilesDataIngestion(), DataIngestionPort)
    assert isinstance(StaticWeatherProvider(), WeatherProviderPort)
