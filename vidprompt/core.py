"""日本語 → 英語翻訳 → 動画生成プロンプト化 のパイプライン。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from .targets import Target, get_target


class ChatModel(Protocol):
    def chat(self, system: str, user: str, *, json_schema: dict[str, Any] | None = None,
             temperature: float = 0.4) -> str: ...


TRANSLATE_SYSTEM = (
    "You are a professional Japanese-to-English translator. Translate the user's Japanese text "
    "into natural, accurate English. Preserve every detail and nuance; do not add new content. "
    "Output only the English translation, nothing else."
)

PROMPT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "action": {"type": "string"},
        "setting": {"type": "string"},
        "camera": {"type": "string"},
        "lighting": {"type": "string"},
        "style": {"type": "string"},
        "mood": {"type": "string"},
        "prompt": {"type": "string"},
        "negative_prompt": {"type": "string"},
    },
    "required": ["subject", "action", "setting", "camera", "lighting", "style", "mood",
                 "prompt", "negative_prompt"],
}


def build_prompt_system(target: Target, duration: int | None, aspect: str | None,
                        style_hint: str | None) -> str:
    extras = []
    if duration:
        extras.append(f"The clip is about {duration} seconds long; describe action that fits that length.")
    if aspect:
        extras.append(f"Compose for a {aspect} aspect ratio.")
    if style_hint:
        extras.append(f"Apply this visual style: {style_hint}.")
    neg = ("Also provide a short comma-separated negative_prompt of artifacts to avoid "
           "(e.g. blurry, distorted hands, text, watermark)."
           if target.supports_negative else
           "This model does not use negative prompts; set negative_prompt to an empty string.")
    return (
        "You are an expert prompt engineer for AI text-to-video models.\n"
        f"Target model: {target.label}.\n"
        f"{target.guidance}\n"
        f"The final 'prompt' field must be in English and at most {target.max_words} words. "
        "Fill in plausible visual details the user left unspecified (camera, lighting, style), "
        "but never contradict the user's description. Describe only what can be seen or heard; "
        "avoid abstract statements. "
        + " ".join(extras) + " " + neg +
        "\nRespond with JSON only, matching the given schema. All fields in English."
    )


@dataclass
class Result:
    japanese: str
    english: str
    target: str
    prompt: str
    negative_prompt: str = ""
    elements: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"モデル出力からJSONを取得できませんでした: {text[:200]}")
    return json.loads(text[start:end + 1])


def translate(model: ChatModel, japanese: str) -> str:
    return model.chat(TRANSLATE_SYSTEM, japanese, temperature=0.1).strip()


def generate(
    model: ChatModel,
    japanese: str,
    target: str = "generic",
    *,
    duration: int | None = None,
    aspect: str | None = None,
    style_hint: str | None = None,
) -> Result:
    japanese = japanese.strip()
    if not japanese:
        raise ValueError("入力テキストが空です")
    tgt = get_target(target)
    english = translate(model, japanese)
    system = build_prompt_system(tgt, duration, aspect, style_hint)
    user = f"Scene description (translated from Japanese):\n{english}\n\nOriginal Japanese:\n{japanese}"
    data = _parse_json(model.chat(system, user, json_schema=PROMPT_SCHEMA, temperature=0.6))
    elements = {k: str(data.get(k, "")).strip() for k in
                ("subject", "action", "setting", "camera", "lighting", "style", "mood")}
    return Result(
        japanese=japanese,
        english=english,
        target=tgt.key,
        prompt=str(data.get("prompt", "")).strip(),
        negative_prompt=str(data.get("negative_prompt", "")).strip() if tgt.supports_negative else "",
        elements=elements,
    )
