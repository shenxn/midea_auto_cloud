# Verified Colmo central AC cloud mappings

This fork adds exact mappings for CAKW71/22/36/28ZN1C1-9Ⅱ, SN8
22397061 / 22397067 / 22397057 / 22397063. The 28 model previously fell back to
the generic central-AC template; all four now share the existing Colmo climate
model, including its target humidity and manufacturer-specific drying modes.

New entities: indoor CO2 (ppm), PM2.5 (µg/m³), TVOC index (unitless), target
humidity, follow-body sensing, breezeless, purification and moisturizing care.
The running fan-speed percentage no longer has a physical wind-speed class.
Controls are gated by the corresponding reported capability bit. They explicitly
use the single-control route supported by these four devices.

The manufacturer's 2026041601 exact-model app defines moisturizing care ON as
female_care=1, temperature=26, small_temperature=0, dehumidity=60 and
airoptimization=off. OFF only clears female_care. The selection label discloses
the temperature/humidity change. Turning it off does not restore old setpoints.
TVOC is an index, not µg/m³ or ppb. Shared new-air-module controls are not added
as duplicate controls of the separately integrated ventilation system.

Evidence: exact-model app commands, 2025102801 model protocol, and current cloud
status. Private vendor scripts, account data and household identifiers are not
committed. No new LAN discovery, transport or local enrollment is implemented.
