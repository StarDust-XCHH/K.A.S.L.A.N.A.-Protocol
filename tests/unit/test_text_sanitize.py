from kaslana.core.text_sanitize import strip_parenthetical_asides


def test_strip_parenthetical_asides_removes_cn_and_en() -> None:
    text = "早安呀（心里有点紧张）该起床啦。(小声嘀咕) 今天也要元气满满哦。"

    assert strip_parenthetical_asides(text) == "早安呀该起床啦。 今天也要元气满满哦。"


def test_strip_parenthetical_asides_handles_nested_passes() -> None:
    text = "你好（外层（内层）结束）世界"

    assert strip_parenthetical_asides(text) == "你好世界"
