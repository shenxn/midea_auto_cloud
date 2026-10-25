# Exact cloud mappings for four household models

These mappings target CWRC-S1000 (63200872), CDG16QA83K (7600002B),
CXEP930W-C3 AIR (730006AE), and JSLQ27-CTE816 (5111102Z). They leave the
fallback templates and all AC mappings intact. No LAN transport is added.

Evidence includes live reported fields, model-specific manufacturer Lua codecs
ED 2025072901 / E1 2024042301 / B6 2025101401 / E3 2023071202, and the
exact-model app bundles. Private captures, vendor bundles and household
identifiers are not committed.

- Purifier: remove boiler/softener placeholders, correct the leakage attribute
  and RO/PCB labels, expose fresh-water and antifreeze settings plus diagnostics.
  The exact 63200872 app does not expose the generic quantitative presets or
  gesture settings: those reported values are read-only, not invented controls.
  Washing and draining remain available but are not activated by deployment.
  Buzzer is read-only: a reversible live test did not confirm its write, and
  the original state was restored.
- Dishwasher: show neutral gear as idle/stop, support reported zero storage time,
  expose stage/count values without collapsing them to booleans, and add child
  lock, beep, knock-opening and diagnostic fields. Selecting a wash program
  starts it; selecting idle stops/powers off. Automatic opening and the light
  strip are read-only until an independent supported command is established.
- Hood: use the proper control/setting routing metadata, add curtain/linkage/
  smoke/AI settings and reminders, remove duplicated lighting and unwritable
  pressure selection. Preserve the existing stove integration pending separate
  b7 telemetry verification. Label calculated energy as estimated.
- Heater: fix gas_lift_precent and explicit no-error display; retain current
  bath level/personal temperature when controlling those modes; use numeric
  bubble values. Add a high-temperature-lock control, reported voice state and other
  diagnostics. Remove unreported lamps and unsupported mode choices. Machine
  type/capacity/power level are diagnostic, not speculative setters. Voice
  writes were not confirmed while the heater was off, so voice stays read-only;
  the heater was not powered on just to test that setting.

Only explicitly listed model control_keys bypass the reported-attribute filter.
Sensor value_map is opt-in; other models retain their existing missing-value
handling. Regression tests check exact selection, state interpretation and
actual entity command payloads. Offline vendor-codec checks additionally catch
commands that encode identically or omit required parameters. Encoding success
is not a claim that every physical operation has been executed.
