import os
import unittest
from unittest.mock import patch

from scripts.voiceover import PROFILES, build_narration, choose_voice_profile, configured_profiles


class VoiceProfileTests(unittest.TestCase):
    def test_ayanokoji_and_johan_are_distinct_profiles(self):
        self.assertNotEqual(PROFILES["ayanokoji-inspired"]["settings"], PROFILES["johan-inspired"]["settings"])
        self.assertNotEqual(PROFILES["ayanokoji-inspired"]["env"], PROFILES["johan-inspired"]["env"])

    def test_auto_selects_only_configured_profiles(self):
        env = {
            "VOICE_ID_AYANOKOJI_INSPIRED": "voice-a",
            "VOICE_ID_JOHAN_INSPIRED": "voice-b",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(set(configured_profiles()), {"ayanokoji-inspired", "johan-inspired"})
            self.assertIn(choose_voice_profile("auto"), {"ayanokoji-inspired", "johan-inspired"})

    def test_auto_requires_a_configured_voice(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "No voice profiles configured"):
                choose_voice_profile("auto")

    def test_psychology_narration_is_non_diagnostic(self):
        text = build_narration("Confidence vs arrogance", "Know the difference", mode="psychology")
        self.assertIn("A single behavior never defines an entire person", text)

    def test_character_narration(self):
        self.assertIn("Gojo, Sukuna", build_narration("Gojo vs Sukuna", "Who wins?", characters=["Gojo", "Sukuna"]))


if __name__ == "__main__":
    unittest.main()
