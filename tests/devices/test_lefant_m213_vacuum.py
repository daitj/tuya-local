from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_RETURNING,
    SUPPORT_BATTERY,
    SUPPORT_CLEAN_SPOT,
    SUPPORT_LOCATE,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_SEND_COMMAND,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STATUS,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
)
from homeassistant.const import (
    AREA_SQUARE_METERS,
    TIME_MINUTES,
)

from ..const import LEFANT_M213_VACUUM_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

POWER_DPS = "1"
SWITCH_DPS = "2"
STATUS_DPS = "3"
DIRECTION_DPS = "4"
UNKNOWN5_DPS = "5"
BATTERY_DPS = "6"
LOCATE_DPS = "13"
AREA_DPS = "16"
TIME_DPS = "17"
ERROR_DPS = "18"
UNKNOWN101_DPS = "101"
UNKNOWN102_DPS = "102"
UNKNOWN103_DPS = "103"
UNKNOWN104_DPS = "104"
UNKNOWN106_DPS = "106"
UNKNOWN108_DPS = "108"


class TestLefantM213Vacuum(MultiSensorTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("lefant_m213_vacuum.yaml", LEFANT_M213_VACUUM_PAYLOAD)
        self.subject = self.entities.get("vacuum")
        self.setUpMultiSensors(
            [
                {
                    "dps": AREA_DPS,
                    "name": "sensor_clean_area",
                    "unit": AREA_SQUARE_METERS,
                },
                {
                    "dps": TIME_DPS,
                    "name": "sensor_clean_time",
                    "unit": TIME_MINUTES,
                },
            ],
        )
        self.mark_secondary(["sensor_clean_area", "sensor_clean_time"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_STATE
            | SUPPORT_STATUS
            | SUPPORT_SEND_COMMAND
            | SUPPORT_BATTERY
            | SUPPORT_TURN_ON
            | SUPPORT_TURN_OFF
            | SUPPORT_START
            | SUPPORT_PAUSE
            | SUPPORT_LOCATE
            | SUPPORT_RETURN_HOME
            | SUPPORT_CLEAN_SPOT,
        )

    def test_battery_level(self):
        self.dps[BATTERY_DPS] = 50
        self.assertEqual(self.subject.battery_level, 50)

    def test_status(self):
        self.dps[STATUS_DPS] = "standby"
        self.assertEqual(self.subject.status, "standby")
        self.dps[STATUS_DPS] = "smart"
        self.assertEqual(self.subject.status, "smart")
        self.dps[STATUS_DPS] = "chargego"
        self.assertEqual(self.subject.status, "return_to_base")
        self.dps[STATUS_DPS] = "random"
        self.assertEqual(self.subject.status, "random")
        self.dps[STATUS_DPS] = "wall_follow"
        self.assertEqual(self.subject.status, "wall_follow")
        self.dps[STATUS_DPS] = "spiral"
        self.assertEqual(self.subject.status, "clean_spot")

    def test_state(self):
        self.dps[POWER_DPS] = True
        self.dps[SWITCH_DPS] = True
        self.dps[ERROR_DPS] = 0
        self.dps[STATUS_DPS] = "return_to_base"
        self.assertEqual(self.subject.state, STATE_RETURNING)
        self.dps[STATUS_DPS] = "standby"
        self.assertEqual(self.subject.state, STATE_DOCKED)
        self.dps[STATUS_DPS] = "random"
        self.assertEqual(self.subject.state, STATE_CLEANING)
        self.dps[POWER_DPS] = False
        self.assertEqual(self.subject.state, STATE_DOCKED)
        self.dps[POWER_DPS] = True
        self.dps[SWITCH_DPS] = False
        self.assertEqual(self.subject.state, STATE_DOCKED)
        self.dps[ERROR_DPS] = 1
        self.assertEqual(self.subject.state, STATE_ERROR)

    async def test_async_turn_on(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True},
        ):
            await self.subject.async_turn_on()

    async def test_async_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: False},
        ):
            await self.subject.async_turn_off()

    async def test_async_toggle(self):
        self.dps[POWER_DPS] = False
        async with assert_device_properties_set(
            self.subject._device,
            {POWER_DPS: True},
        ):
            await self.subject.async_toggle()

    async def test_async_start(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: True},
        ):
            await self.subject.async_start()

    async def test_async_pause(self):
        async with assert_device_properties_set(
            self.subject._device,
            {SWITCH_DPS: False},
        ):
            await self.subject.async_pause()

    async def test_async_return_to_base(self):
        async with assert_device_properties_set(
            self.subject._device,
            {STATUS_DPS: "chargego"},
        ):
            await self.subject.async_return_to_base()

    async def test_async_clean_spot(self):
        async with assert_device_properties_set(
            self.subject._device,
            {STATUS_DPS: "spiral"},
        ):
            await self.subject.async_clean_spot()

    async def test_async_locate(self):
        async with assert_device_properties_set(
            self.subject._device,
            {LOCATE_DPS: True},
        ):
            await self.subject.async_locate()

    async def test_async_send_standby_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {STATUS_DPS: "standby"},
        ):
            await self.subject.async_send_command("standby")

    async def test_async_send_smart_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {STATUS_DPS: "smart"},
        ):
            await self.subject.async_send_command("smart")

    async def test_async_send_random_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {STATUS_DPS: "random"},
        ):
            await self.subject.async_send_command("random")

    async def test_async_send_wall_follow_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {STATUS_DPS: "wall_follow"},
        ):
            await self.subject.async_send_command("wall_follow")

    async def test_async_send_reverse_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {DIRECTION_DPS: "backward"},
        ):
            await self.subject.async_send_command("reverse")

    async def test_async_send_left_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {DIRECTION_DPS: "turn_left"},
        ):
            await self.subject.async_send_command("left")

    async def test_async_send_right_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {DIRECTION_DPS: "turn_right"},
        ):
            await self.subject.async_send_command("right")

    async def test_async_send_stop_command(self):
        async with assert_device_properties_set(
            self.subject._device,
            {DIRECTION_DPS: "stop"},
        ):
            await self.subject.async_send_command("stop")
