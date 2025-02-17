from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.fan import SUPPORT_PRESET_MODE
from homeassistant.const import (
    PERCENTAGE,
    TIME_MINUTES,
)

from ..const import VORK_VK6067_PURIFIER_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.light import BasicLightTests
from ..mixins.select import BasicSelectTests
from ..mixins.sensor import MultiSensorTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
MODE_DPS = "4"
FILTER_DPS = "5"
LIGHT_DPS = "8"
RESET_DPS = "11"
TIMER_DPS = "18"
COUNTDOWN_DPS = "19"
AQI_DPS = "21"
ERROR_DPS = "22"


class TestVorkVK6267AWPurifier(
    BasicBinarySensorTests,
    BasicLightTests,
    BasicSelectTests,
    BasicSwitchTests,
    MultiSensorTests,
    SwitchableTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("vork_vk6067aw_purifier.yaml", VORK_VK6067_PURIFIER_PAYLOAD)
        self.subject = self.entities["fan"]
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_error"),
            device_class=BinarySensorDeviceClass.PROBLEM,
            testdata=(1, 0),
        )
        self.setUpBasicLight(LIGHT_DPS, self.entities.get("light"))
        self.setUpBasicSelect(
            TIMER_DPS,
            self.entities.get("select_timer"),
            {
                "cancel": "off",
                "1h": "1 hour",
                "2h": "2 hours",
            },
        )
        self.setUpBasicSwitch(RESET_DPS, self.entities.get("switch_filter_reset"))
        self.setUpMultiSensors(
            [
                {
                    "dps": AQI_DPS,
                    "name": "sensor_air_quality",
                    "testdata": ("great", "Great"),
                },
                {
                    "dps": COUNTDOWN_DPS,
                    "name": "sensor_timer",
                    "unit": TIME_MINUTES,
                },
                {
                    "dps": FILTER_DPS,
                    "name": "sensor_filter",
                    "unit": PERCENTAGE,
                },
            ]
        )
        self.mark_secondary(
            [
                "binary_sensor_error",
                "light",
                "select_timer",
                "sensor_air_quality",
                "sensor_filter",
                "sensor_timer",
                "switch_filter_reset",
            ]
        )

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_PRESET_MODE,
        )

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            ["Low", "Mid", "High", "Auto", "Sleep"],
        )

    def test_preset_mode(self):
        self.dps[MODE_DPS] = "low"
        self.assertEqual(self.subject.preset_mode, "Low")
        self.dps[MODE_DPS] = "mid"
        self.assertEqual(self.subject.preset_mode, "Mid")
        self.dps[MODE_DPS] = "high"
        self.assertEqual(self.subject.preset_mode, "High")
        self.dps[MODE_DPS] = "auto"
        self.assertEqual(self.subject.preset_mode, "Auto")
        self.dps[MODE_DPS] = "sleep"
        self.assertEqual(self.subject.preset_mode, "Sleep")

    async def test_set_preset_to_low(self):
        async with assert_device_properties_set(
            self.subject._device,
            {MODE_DPS: "low"},
        ):
            await self.subject.async_set_preset_mode("Low")

    async def test_set_preset_to_auto(self):
        async with assert_device_properties_set(
            self.subject._device,
            {MODE_DPS: "auto"},
        ):
            await self.subject.async_set_preset_mode("Auto")

    async def test_set_preset_to_sleep(self):
        async with assert_device_properties_set(
            self.subject._device,
            {MODE_DPS: "sleep"},
        ):
            await self.subject.async_set_preset_mode("Sleep")
