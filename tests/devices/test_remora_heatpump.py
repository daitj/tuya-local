from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import STATE_UNAVAILABLE

from ..const import REMORA_HEATPUMP_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.climate import TargetTemperatureTests
from .base_device_tests import TuyaDeviceTestCase

HVACMODE_DPS = "1"
TEMPERATURE_DPS = "2"
CURRENTTEMP_DPS = "3"
PRESET_DPS = "4"
ERROR_DPS = "9"


class TestRemoraHeatpump(
    BasicBinarySensorTests, TargetTemperatureTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("remora_heatpump.yaml", REMORA_HEATPUMP_PAYLOAD)
        self.subject = self.entities.get("climate")
        self.setUpTargetTemperature(
            TEMPERATURE_DPS,
            self.subject,
            min=5,
            max=40,
        )
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_water_flow"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.mark_secondary(["binary_sensor_water_flow"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE,
        )

    def test_icon(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.icon, "mdi:hot-tub")
        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.icon, "mdi:hvac-off")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    async def test_legacy_set_temperature_with_preset_mode(self):
        async with assert_device_properties_set(
            self.subject._device, {PRESET_DPS: "cool"}
        ):
            await self.subject.async_set_temperature(preset_mode="Smart Cooling")

    async def test_legacy_set_temperature_with_both_properties(self):
        async with assert_device_properties_set(
            self.subject._device, {TEMPERATURE_DPS: 26, PRESET_DPS: "heat"}
        ):
            await self.subject.async_set_temperature(
                temperature=26, preset_mode="Smart Heating"
            )

    def test_current_temperature(self):
        self.dps[CURRENTTEMP_DPS] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[HVACMODE_DPS] = True
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[HVACMODE_DPS] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[HVACMODE_DPS] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_HEAT])

    async def test_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: True}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device, {HVACMODE_DPS: False}
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    def test_preset_mode(self):
        self.dps[PRESET_DPS] = "heat"
        self.assertEqual(self.subject.preset_mode, "Smart Heating")

        self.dps[PRESET_DPS] = "cool"
        self.assertEqual(self.subject.preset_mode, "Smart Cooling")

        self.dps[PRESET_DPS] = "h_powerful"
        self.assertEqual(self.subject.preset_mode, "Powerful Heating")

        self.dps[PRESET_DPS] = "c_powerful"
        self.assertEqual(self.subject.preset_mode, "Powerful Cooling")

        self.dps[PRESET_DPS] = "h_silent"
        self.assertEqual(self.subject.preset_mode, "Silent Heating")

        self.dps[PRESET_DPS] = "c_silent"
        self.assertEqual(self.subject.preset_mode, "Silent Cooling")

        self.dps[PRESET_DPS] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [
                "Smart Heating",
                "Powerful Heating",
                "Silent Heating",
                "Smart Cooling",
                "Powerful Cooling",
                "Silent Cooling",
            ],
        )

    async def test_set_preset_mode_to_heat(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "heat"},
        ):
            await self.subject.async_set_preset_mode("Smart Heating")

    async def test_set_preset_mode_to_cool(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "cool"},
        ):
            await self.subject.async_set_preset_mode("Smart Cooling")

    async def test_set_preset_mode_to_h_powerful(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "h_powerful"},
        ):
            await self.subject.async_set_preset_mode("Powerful Heating")

    async def test_set_preset_mode_to_c_powerful(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "c_powerful"},
        ):
            await self.subject.async_set_preset_mode("Powerful Cooling")

    async def test_set_preset_mode_to_h_silent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "h_silent"},
        ):
            await self.subject.async_set_preset_mode("Silent Heating")

    async def test_set_preset_mode_to_c_silent(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PRESET_DPS: "c_silent"},
        ):
            await self.subject.async_set_preset_mode("Silent Cooling")

    def test_error_state(self):
        self.dps[ERROR_DPS] = 0
        self.assertEqual(self.subject.extra_state_attributes, {"error": "OK"})

        self.dps[ERROR_DPS] = 1
        self.assertEqual(
            self.subject.extra_state_attributes,
            {"error": "Water Flow Protection"},
        )
        self.dps[ERROR_DPS] = 2
        self.assertEqual(
            self.subject.extra_state_attributes,
            {"error": 2},
        )
