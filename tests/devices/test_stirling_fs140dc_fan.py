from homeassistant.components.fan import (
    SUPPORT_OSCILLATE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
)

from ..const import STIRLING_FS1_FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.switch import SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
PRESET_DPS = "2"
SPEED_DPS = "3"
OSCILLATE_DPS = "5"
TIMER_DPS = "22"


class TestStirlingFS1Fan(SwitchableTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("stirling_fs140dc_fan.yaml", STIRLING_FS1_FAN_PAYLOAD)
        self.subject = self.entities.get("fan")
        self.timer = self.entities.get("select_timer")
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.mark_secondary(["select_timer"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_OSCILLATE | SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED,
        )

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "normal"
        self.assertEqual(self.subject.preset_mode, "normal")

        self.dps[PRESET_DPS] = "nature"
        self.assertEqual(self.subject.preset_mode, "nature")

        self.dps[PRESET_DPS] = "sleep"
        self.assertEqual(self.subject.preset_mode, "sleep")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["normal", "nature", "sleep"],
        )

    async def test_set_preset_mode_to_normal(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "normal"},
        ):
            await self.subject.async_set_preset_mode("normal")

    async def test_set_preset_mode_to_nature(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "nature"},
        ):
            await self.subject.async_set_preset_mode("nature")

    async def test_set_preset_mode_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "sleep"},
        ):
            await self.subject.async_set_preset_mode("sleep")

    def test_oscillating(self):
        self.dps[OSCILLATE_DPS] = False
        self.assertFalse(self.subject.oscillating)

        self.dps[OSCILLATE_DPS] = True
        self.assertTrue(self.subject.oscillating)

        self.dps[OSCILLATE_DPS] = None
        self.assertFalse(self.subject.oscillating)

    async def test_oscillate_off(self):
        async with assert_device_properties_set(
            self.subject._device, {OSCILLATE_DPS: False}
        ):
            await self.subject.async_oscillate(False)

    async def test_oscillate_on(self):
        async with assert_device_properties_set(
            self.subject._device, {OSCILLATE_DPS: True}
        ):
            await self.subject.async_oscillate(True)

    def test_speed(self):
        self.dps[SPEED_DPS] = "4"
        self.assertAlmostEqual(self.subject.percentage, 26.67, 2)

    def test_speed_step(self):
        self.assertAlmostEqual(self.subject.percentage_step, 6.67, 2)
        self.assertEqual(self.subject.speed_count, 15)

    async def test_set_speed(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 5}):
            await self.subject.async_set_percentage(33)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 10}):
            await self.subject.async_set_percentage(64)

    def test_extra_state_attributes(self):
        self.assertEqual(self.subject.extra_state_attributes, {})
        self.assertEqual(self.timer.extra_state_attributes, {})

    def test_timer_options(self):
        self.assertCountEqual(
            self.timer.options,
            [
                "Off",
                "30 minutes",
                "1 hour",
                "1.5 hours",
                "2 hours",
                "2.5 hours",
                "3 hours",
                "3.5 hours",
                "4 hours",
                "4.5 hours",
                "5 hours",
                "5.5 hours",
                "6 hours",
                "6.5 hours",
                "7 hours",
                "7.5 hours",
                "8 hours",
                "8.5 hours",
                "9 hours",
                "9.5 hours",
                "10 hours",
            ],
        )

    def test_timer_current_option(self):
        self.dps[TIMER_DPS] = "0_5"
        self.assertEqual(self.timer.current_option, "30 minutes")

    async def test_select_option(self):
        async with assert_device_properties_set(
            self.timer._device,
            {TIMER_DPS: "4_0"},
        ):
            await self.timer.async_select_option("4 hours")
