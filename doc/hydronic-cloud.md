# Shared Colmo hydronic module over cloud

The selected 22397061 indoor-unit mapping exposes one hydronic climate plus
auxiliary-heat, energy-saving and away switches. The other three exact indoor
unit models do not duplicate this shared module. This is the selected entry for
this installation; installations with multiple same-model units need explicit
primary-entry selection before enabling duplicates.

The air-conditioner climate is unchanged. Water power, water setpoint and
water automatic-temperature fields are separate from air power and temperature.
Setting water temperature (25–60°C, whole degrees) explicitly selects manual
water regulation, as the exact-model app does. All controls use the device's
single-control route. Unsupported water-temperature linkage is not exposed.

A water_model_run_status query supplies tw1_in_water_temp and
tw1_out_water_temp. The climate uses actual outlet water temperature, never
room temperature or the AC setpoint. Its heating action is unknown while on
unless runtime evidence is available; selecting heat is not proof that the
compressor is currently running. An unavailable water reading stays unknown.

The module capability gates availability. The vendor handles the energy-saving
timeout and away-mode behavior; no additional HA timer or automatic startup is
introduced. The module and electric auxiliary heat remain off during deployment.
Tests cover water/air isolation, setpoint bounds, manual coupling and actual
entity methods. Private vendor codecs and live household captures are excluded.

The six hydronic entities are grouped under a separate logical device named
地暖水力模块, with via_device pointing to the selected indoor AC. Their original
unique IDs and entity IDs remain in place so history and automations survive
migration. The logical module does not borrow the indoor unit's serial number
and continues to use its existing cloud coordinator and transport.
