import os
from functools import cache

import hypothesis.strategies as st
from hypothesis import Phase, given, settings

from cereal import car
from opendbc.car import DT_CTRL
from opendbc.car.structs import CarParams

MAX_EXAMPLES = int(os.environ.get("MAX_EXAMPLES", "60"))


@cache
def _car_control_msg_strategy():
  from openpilot.selfdrive.test.fuzzy_generation import FuzzyGenerator

  return FuzzyGenerator(lambda _: None, real_floats=True).generate_struct(car.CarControl.schema)


class TestCarInterfaces:
  # FIXME: Due to the lists used in carParams, Phase.target is very slow and will cause
  #  many generated examples to overrun when max_examples > ~20, don't use it
  @settings(max_examples=MAX_EXAMPLES, deadline=None,
            phases=(Phase.reuse, Phase.generate, Phase.shrink))
  @given(data=st.data())
  def test_car_interfaces(self, car_name, data):
    from opendbc.car.tests.test_car_interfaces import get_fuzzy_car_interface
    from openpilot.selfdrive.controls.lib.latcontrol_angle import LatControlAngle
    from openpilot.selfdrive.controls.lib.latcontrol_pid import LatControlPID
    from openpilot.selfdrive.controls.lib.latcontrol_torque import LatControlTorque
    from openpilot.selfdrive.controls.lib.longcontrol import LongControl

    car_interface = get_fuzzy_car_interface(car_name, data.draw)
    car_params = car_interface.CP.as_reader()

    cc_msg = data.draw(_car_control_msg_strategy())
    # Run car interface
    now_nanos = 0
    CC = car.CarControl.new_message(**cc_msg)
    CC = CC.as_reader()
    for _ in range(10):
      car_interface.update([])
      car_interface.apply(CC, now_nanos)
      now_nanos += DT_CTRL * 1e9  # 10 ms

    CC = car.CarControl.new_message(**cc_msg)
    CC.enabled = True
    CC.latActive = True
    CC.longActive = True
    CC = CC.as_reader()
    for _ in range(10):
      car_interface.update([])
      car_interface.apply(CC, now_nanos)
      now_nanos += DT_CTRL * 1e9  # 10ms

    LongControl(car_params)
    if car_params.steerControlType == CarParams.SteerControlType.angle:
      LatControlAngle(car_params, car_interface, DT_CTRL)
    elif car_params.lateralTuning.which() == 'pid':
      LatControlPID(car_params, car_interface, DT_CTRL)
    elif car_params.lateralTuning.which() == 'torque':
      LatControlTorque(car_params, car_interface, DT_CTRL)
