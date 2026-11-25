"""出力先の動画生成AIごとの整形ルール。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    key: str
    label: str
    guidance: str          # LLM に渡す書き方の指示
    max_words: int
    supports_negative: bool


TARGETS: dict[str, Target] = {
    "generic": Target(
        "generic", "汎用",
        "Write one rich, cinematic paragraph in present tense: subject, action, setting, "
        "camera movement, lighting, style and mood.",
        120, True,
    ),
    "sora": Target(
        "sora", "OpenAI Sora",
        "Write a vivid narrative paragraph like a film director's shot description. "
        "Describe how the scene unfolds over time, with specific camera language "
        "(e.g. 'slow dolly in', 'aerial tracking shot') and lighting.",
        150, False,
    ),
    "veo": Target(
        "veo", "Google Veo",
        "Write a concise, detailed paragraph: shot type and camera motion first, then subject, "
        "action, environment, lighting and visual style. Mention ambient sound if relevant.",
        120, True,
    ),
    "runway": Target(
        "runway", "Runway Gen",
        "Use the structure '[camera movement]: [establishing scene]. [additional details].' "
        "Keep it direct and visual; avoid negative phrasing.",
        80, False,
    ),
    "kling": Target(
        "kling", "Kling",
        "Use the structure 'subject + subject motion + scene + camera language + lighting + atmosphere'. "
        "Short comma-separated descriptive phrases are fine.",
        100, True,
    ),
    "wan": Target(
        "wan", "Wan / HunyuanVideo (ローカル系)",
        "Write a detailed single paragraph with explicit subject appearance, motion, background, "
        "camera angle, lighting and style keywords, suitable for open-source video diffusion models.",
        120, True,
    ),
}


def get_target(key: str) -> Target:
    try:
        return TARGETS[key]
    except KeyError:
        raise ValueError(f"未知のターゲット '{key}'. 選択肢: {', '.join(TARGETS)}") from None
