import json
import unittest

from vidprompt.core import _parse_json, generate
from vidprompt.targets import TARGETS


class FakeModel:
    def __init__(self):
        self.calls = []

    def chat(self, system, user, *, json_schema=None, temperature=0.4):
        self.calls.append((system, user, json_schema))
        if json_schema is None:
            return "A Shiba Inu runs along the beach at dusk."
        return json.dumps({
            "subject": "a Shiba Inu", "action": "running", "setting": "beach at dusk",
            "camera": "side tracking shot", "lighting": "golden hour", "style": "cinematic",
            "mood": "joyful", "prompt": "Side tracking shot of a joyful Shiba Inu running on a beach.",
            "negative_prompt": "blurry, watermark",
        })


class CoreTest(unittest.TestCase):
    def test_generate_pipeline(self):
        m = FakeModel()
        r = generate(m, "夕暮れの海辺を走る柴犬", "generic", duration=5, aspect="16:9")
        self.assertEqual(r.english, "A Shiba Inu runs along the beach at dusk.")
        self.assertIn("Shiba Inu", r.prompt)
        self.assertEqual(r.negative_prompt, "blurry, watermark")
        self.assertEqual(len(m.calls), 2)
        self.assertIn("5 seconds", m.calls[1][0])
        self.assertIn("16:9", m.calls[1][0])

    def test_negative_dropped_for_unsupported_target(self):
        r = generate(FakeModel(), "テスト", "sora")
        self.assertFalse(TARGETS["sora"].supports_negative)
        self.assertEqual(r.negative_prompt, "")

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            generate(FakeModel(), "   ")

    def test_unknown_target(self):
        with self.assertRaises(ValueError):
            generate(FakeModel(), "テスト", "nope")

    def test_parse_json_with_fence(self):
        self.assertEqual(_parse_json('```json\n{"a": 1}\n```'), {"a": 1})


if __name__ == "__main__":
    unittest.main()
