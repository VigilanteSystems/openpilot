def pytest_generate_tests(metafunc):
  """Parametrize test_car_interfaces with all car platforms plus MOCK."""
  if "car_name" in metafunc.fixturenames:
    from opendbc.car.mock.values import CAR as MOCK
    from opendbc.car.values import PLATFORMS

    metafunc.parametrize("car_name", sorted(PLATFORMS) + [MOCK.MOCK])
