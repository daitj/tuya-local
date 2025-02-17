"""
Platform to control Tuya lights.
Initially based on the secondary panel lighting control on some climate
devices, so only providing simple on/off control.
"""
from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_RGBW_COLOR,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_ONOFF,
    COLOR_MODE_RGBW,
    COLOR_MODE_UNKNOWN,
    COLOR_MODE_WHITE,
    SUPPORT_EFFECT,
    VALID_COLOR_MODES,
)
import homeassistant.util.color as color_util

import logging
from struct import pack, unpack

from ..device import TuyaLocalDevice
from ..helpers.device_config import TuyaEntityConfig
from ..helpers.mixin import TuyaLocalEntity

_LOGGER = logging.getLogger(__name__)


class TuyaLocalLight(TuyaLocalEntity, LightEntity):
    """Representation of a Tuya WiFi-connected light."""

    def __init__(self, device: TuyaLocalDevice, config: TuyaEntityConfig):
        """
        Initialize the light.
        Args:
            device (TuyaLocalDevice): The device API instance.
            config (TuyaEntityConfig): The configuration for this entity.
        """
        dps_map = self._init_begin(device, config)
        self._switch_dps = dps_map.pop("switch", None)
        self._brightness_dps = dps_map.pop("brightness", None)
        self._color_mode_dps = dps_map.pop("color_mode", None)
        self._color_temp_dps = dps_map.pop("color_temp", None)
        self._rgbhsv_dps = dps_map.pop("rgbhsv", None)
        self._effect_dps = dps_map.pop("effect", None)
        self._init_end(dps_map)

    @property
    def supported_color_modes(self):
        """Return the supported color modes for this light."""
        if self._color_mode_dps:
            return [
                mode
                for mode in self._color_mode_dps.values(self._device)
                if mode in VALID_COLOR_MODES
            ]
        else:
            mode = self.color_mode
            if mode and mode != COLOR_MODE_UNKNOWN:
                return [mode]

        return []

    @property
    def supported_features(self):
        """Return the supported features for this light."""
        if self.effect_list:
            return SUPPORT_EFFECT
        else:
            return 0

    @property
    def color_mode(self):
        """Return the color mode of the light"""
        if self._color_mode_dps:
            mode = self._color_mode_dps.get_value(self._device)
            if mode in VALID_COLOR_MODES:
                return mode

        if self._rgbhsv_dps:
            return COLOR_MODE_RGBW
        elif self._color_temp_dps:
            return COLOR_MODE_COLOR_TEMP
        elif self._brightness_dps:
            return COLOR_MODE_BRIGHTNESS
        elif self._switch_dps:
            return COLOR_MODE_ONOFF
        else:
            return COLOR_MODE_UNKNOWN

    @property
    def color_temp(self):
        """Return the color temperature in mireds"""
        if self._color_temp_dps:
            unscaled = self._color_temp_dps.get_value(self._device)
            r = self._color_temp_dps.range(self._device)
            if r:
                return round(unscaled * 347 / (r["max"] - r["min"]) + 153 - r["min"])
            else:
                return unscaled

    @property
    def is_on(self):
        """Return the current state."""
        if self._switch_dps:
            return self._switch_dps.get_value(self._device)
        elif self._brightness_dps:
            b = self.brightness
            return isinstance(b, int) and b > 0
        else:
            # There shouldn't be lights without control, but if there are,
            # assume always on if they are responding
            return self.available

    @property
    def brightness(self):
        """Get the current brightness of the light"""
        if self._brightness_dps:
            return self._brightness_dps.get_value(self._device)

    @property
    def rgbw_color(self):
        """Get the current RGBW color of the light"""
        if self._rgbhsv_dps:
            # color data in hex format RRGGBBHHHHSSVV (14 digit hex)
            # can also be base64 encoded.
            # Either RGB or HSV can be used.
            color = self._rgbhsv_dps.decoded_value(self._device)

            fmt = self._rgbhsv_dps.format
            if fmt:
                vals = unpack(fmt.get("format"), color)
                rgbhsv = {}
                idx = 0
                for v in vals:
                    # Range in HA is 0-100 for s, 0-255 for rgb and v, 0-360
                    # for h
                    n = fmt["names"][idx]
                    r = fmt["ranges"][idx]
                    if r["min"] != 0:
                        raise AttributeError(
                            f"Unhandled minimum range for {n} in RGBW value"
                        )
                    mx = r["max"]
                    scale = 1
                    if n == "h":
                        scale = 360 / mx
                    elif n == "s":
                        scale = 100 / mx
                    else:
                        scale = 255 / mx

                    rgbhsv[n] = round(scale * v)
                    idx += 1

                h = rgbhsv["h"]
                s = rgbhsv["s"]
                # convert RGB from H and S to seperate out the V component
                r, g, b = color_util.color_hs_to_RGB(h, s)
                w = rgbhsv["v"]
                return (r, g, b, w)

    @property
    def effect_list(self):
        """Return the list of valid effects for the light"""
        if self._effect_dps:
            return self._effect_dps.values(self._device)
        elif self._color_mode_dps:
            return [
                effect
                for effect in self._color_mode_dps.values(self._device)
                if effect not in VALID_COLOR_MODES
            ]

    @property
    def effect(self):
        """Return the current effect setting of this light"""
        if self._effect_dps:
            return self._effect_dps.get_value(self._device)
        elif self._color_mode_dps:
            mode = self._color_mode_dps.get_value(self._device)
            if mode not in VALID_COLOR_MODES:
                return mode

    async def async_turn_on(self, **params):
        settings = {}
        color_mode = params.get(ATTR_COLOR_MODE, self.color_mode)

        if self._color_temp_dps and ATTR_COLOR_TEMP in params:
            if ATTR_COLOR_MODE not in params:
                color_mode = COLOR_MODE_WHITE
            if self._color_mode_dps:
                _LOGGER.debug("Auto setting color mode to WHITE for color temp")
                settings = {
                    **settings,
                    **self._color_mode_dps.get_values_to_set(self._device, color_mode),
                }
            color_temp = params.get(ATTR_COLOR_TEMP)
            r = self._color_temp_dps.range(self._device)

            if r and color_temp:
                color_temp = round(
                    (color_temp - 153 + r["min"]) * (r["max"] - r["min"]) / 347
                )

            _LOGGER.debug(f"Setting color temp to {color_temp}")
            settings = {
                **settings,
                **self._color_temp_dps.get_values_to_set(self._device, color_temp),
            }
        elif self._rgbhsv_dps and (
            ATTR_RGBW_COLOR in params
            or (ATTR_BRIGHTNESS in params and color_mode == COLOR_MODE_RGBW)
        ):
            if ATTR_COLOR_MODE not in params:
                color_mode = COLOR_MODE_RGBW
            if self._color_mode_dps:
                _LOGGER.debug("Auto setting color mode to RGBW")
                settings = {
                    **settings,
                    **self._color_mode_dps.get_values_to_set(self._device, color_mode),
                }
            rgbw = params.get(ATTR_RGBW_COLOR, self.rgbw_color or (0, 0, 0, 0))
            brightness = params.get(ATTR_BRIGHTNESS, rgbw[3])
            fmt = self._rgbhsv_dps.format
            if rgbw and fmt:
                rgb = (rgbw[0], rgbw[1], rgbw[2])
                hs = color_util.color_RGB_to_hs(rgbw[0], rgbw[1], rgbw[2])
                rgbhsv = {
                    "r": rgb[0],
                    "g": rgb[1],
                    "b": rgb[2],
                    "h": hs[0],
                    "s": hs[1],
                    "v": brightness,
                }
                _LOGGER.debug(
                    f"Setting RGBW as {rgb[0]},{rgb[1]},{rgb[2]},{hs[0]},{hs[1]},{brightness}"
                )
                ordered = []
                idx = 0
                for n in fmt["names"]:
                    r = fmt["ranges"][idx]
                    scale = 1
                    if n == "s":
                        scale = r["max"] / 100
                    elif n == "h":
                        scale = r["max"] / 360
                    else:
                        scale = r["max"] / 255
                    ordered.append(round(rgbhsv[n] * scale))
                    idx += 1
                binary = pack(fmt["format"], *ordered)
                settings = {
                    **settings,
                    **self._rgbhsv_dps.get_values_to_set(
                        self._device,
                        self._rgbhsv_dps.encode_value(binary),
                    ),
                }
        elif self._color_mode_dps and ATTR_COLOR_MODE in params:
            if color_mode:
                _LOGGER.debug(f"Explicitly setting color mode to {color_mode}")
                settings = {
                    **settings,
                    **self._color_mode_dps.get_values_to_set(self._device, color_mode),
                }
            elif not self._effect_dps:
                effect = params.get(ATTR_EFFECT)
                if effect:
                    _LOGGER.debug(f"Emulating effect using color mode of {effect}")
                    settings = {
                        **settings,
                        **self._color_mode_dps.get_values_to_set(
                            self._device,
                            effect,
                        ),
                    }

        if (
            ATTR_BRIGHTNESS in params
            and color_mode != COLOR_MODE_RGBW
            and self._brightness_dps
        ):
            bright = params.get(ATTR_BRIGHTNESS)
            _LOGGER.debug(f"Setting brightness to {bright}")
            settings = {
                **settings,
                **self._brightness_dps.get_values_to_set(
                    self._device,
                    bright,
                ),
            }

        if self._switch_dps:
            settings = {
                **settings,
                **self._switch_dps.get_values_to_set(self._device, True),
            }

        if self._effect_dps:
            effect = params.get(ATTR_EFFECT, None)
            if effect:
                _LOGGER.debug(f"Setting effect to {effect}")
                settings = {
                    **settings,
                    **self._effect_dps.get_values_to_set(
                        self._device,
                        effect,
                    ),
                }

        await self._device.async_set_properties(settings)

    async def async_turn_off(self):
        if self._switch_dps:
            await self._switch_dps.async_set_value(self._device, False)
        elif self._brightness_dps:
            await self._brightness_dps.async_set_value(self._device, 0)
        else:
            raise NotImplementedError()

    async def async_toggle(self):
        disp_on = self.is_on

        await (self.async_turn_on() if not disp_on else self.async_turn_off())
