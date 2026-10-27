import unittest
from unittest.mock import patch

from scripts.voiceover import PROFILES, build_narration, choose_voice_profile, configured_profiles


class VoiceProfileTests(unittest.TestCase):
    def test_ayanokoji_and_johan_are_distinct_offline_profiles(self):
        self.assertNotEqual(PROFILES["ayanokoji-inspired"]["voice"], PROFILES["johan-inspired"]["voice"])
        self.assertNotEqual(PROFILES["ayanokoji-inspired"]["speed"], PROFILES["johan-inspired"]["speed"])
        self.assertNotEqual(PROFILES["ayanokoji-inspired"]["pitch"], PROFILES["johan-inspired"]["pitch"])

    def test_auto_selects_available_local_profiles(self):
        with patch("scripts.voiceover.shutil.which", return_value="/usr/bin/espeak-ng"):
            self.assertEqual(set(configured_profiles()), set(PROFILES))
            self.assertIn(choose_voice_profile("auto"), set(PROFILES))

    def test_auto_fails_clearly_if_espeak_missing(self):
        with patch("scripts.voiceover.shutil.which", return_value=None):
            self.assertEqual(configured_profiles(), [])
            with self.assertRaisesRegex(RuntimeError, "espeak-ng is not installed"):
                choose_voice_profile("auto")

    def test_psychology_narration_is_non_diagnostic(self):
        text = build_narration("Confidence vs arrogance", "Know the difference", mode="psychology")
        self.assertIn("A single behavior never defines an entire person", text)

    def test_character_narration(self):
        self.assertIn("Gojo, Sukuna", build_narration("Gojo vs Sukuna", "Who wins?", characters=["Gojo", "Sukuna"]))


if __name__ == "__main__":
    unittest.main()
