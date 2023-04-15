import os
import sys
import unittest

from colormath.color_objects import HSVColor

sys.path.append(os.getcwd())

import color_utils as cutils
from enums import DeviceModel
from lighting import Config, State, config, types, Abstract


class TestColorOverride(unittest.TestCase):
    "Testing the color override functionality of abstract lights."

    def setUp(self):
        self.config_on  = Config(toggled_on=config.Override.perm(True))
        self.regular_on = types.regular("A", "B", "C", "D", DeviceModel.HueColor, self.config_on)
        # Always reset in case some test case changed their value.
        self.red                = HSVColor(hsv_h=0.00, hsv_s=1.00, hsv_v=1.0)
        self.blue               = HSVColor(hsv_h=0.66, hsv_s=1.00, hsv_v=1.0)
        self.shade_of_blue      = HSVColor(hsv_h=0.55, hsv_s=0.77, hsv_v=0.2)
        self.shade_of_green     = HSVColor(hsv_h=0.36, hsv_s=0.27, hsv_v=0.7)
        self.shade_of_red       = HSVColor(hsv_h=0.05, hsv_s=0.90, hsv_v=0.8)
        self.white              = HSVColor(hsv_h=0.00, hsv_s=0.00, hsv_v=1.0)

    def _override_and_resolve(
        self,
        light: Abstract,
        desired: HSVColor
    ) -> State:
        light.update_color(desired=desired)
        return config.resolve(light.config, State.max())

    def test_single_simple(self):
        "Checks if the override workes when the original color is white; simple."
        light = self.regular_on
        res = self._override_and_resolve(light, desired=self.red)
        self.assertTrue(cutils.equal(res.color, self.red))

    def test_single_complex(self):
        "Checks if the override workes if the actual and desired colors are quite dissimilar."
        light   = self.regular_on
        desired = self.shade_of_blue
        self._override_and_resolve(light, desired=desired)
        res = self._override_and_resolve(light, desired=self.shade_of_blue)
        print(res.color)
        print(self.shade_of_blue)
        self.assertTrue(cutils.equal(res.color, self.shade_of_blue))

    def test_idempotency(self):
        "Checks if the accommodation is idempotent."
        light   = self.regular_on
        desired = self.shade_of_blue
        self._override_and_resolve(light, desired=desired)
        res = self._override_and_resolve(light, desired=self.shade_of_blue)
        self.assertTrue(cutils.equal(res.color, self.shade_of_blue))
        res = self._override_and_resolve(light, desired=self.shade_of_blue)
        self.assertTrue(cutils.equal(res.color, self.shade_of_blue))

if __name__ == '__main__':
    unittest.main()
