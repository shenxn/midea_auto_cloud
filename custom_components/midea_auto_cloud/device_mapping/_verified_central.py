"""Cloud mappings verified against the Colmo 2026041601 app and live status.

Keep these four exact models separate from unrelated central AC families.
The device remains cloud controlled; this module adds no local transport.
"""

from copy import deepcopy

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import Platform

VERIFIED_CENTRAL_MODELS = ("22397061", "22397067", "22397057", "22397063")


def extend_central_models(mappings: dict) -> dict:
    """Prepend exact-model mappings without mutating shared fallback templates."""
    base = next(
        value
        for key, value in mappings.items()
        if isinstance(key, tuple) and "22397061" in key
    )
    result = {}
    for model in VERIFIED_CENTRAL_MODELS:
        config = deepcopy(base)
        entities = config["entities"]
        sensors = entities[Platform.SENSOR]
        sensors["wind_speed_real"].pop("device_class", None)
        sensors["wind_speed_real"]["name"] = "运行风速"
        sensors.update(
            {
                "indoor_co2": {
                    "name": "室内 CO₂",
                    "device_class": SensorDeviceClass.CO2,
                    "unit_of_measurement": "ppm",
                    "state_class": SensorStateClass.MEASUREMENT,
                },
                "indoor_pm25": {
                    "name": "室内 PM2.5",
                    "device_class": SensorDeviceClass.PM25,
                    "unit_of_measurement": "µg/m³",
                    "state_class": SensorStateClass.MEASUREMENT,
                },
                "indoor_tvoc": {
                    "name": "室内 TVOC 指数",
                    "state_class": SensorStateClass.MEASUREMENT,
                    "icon": "mdi:air-filter",
                },
                "dehumidity": {
                    "name": "目标湿度",
                    "device_class": SensorDeviceClass.HUMIDITY,
                    "unit_of_measurement": "%",
                    "state_class": SensorStateClass.MEASUREMENT,
                },
            }
        )
        switches = entities[Platform.SWITCH]
        for key, name, capability in (
            ("follow_body_sense", "随身感", "has_follow_body_sense"),
            ("no_wind_sense", "无风感", "has_no_wind_sense"),
            ("inner_purifier", "净化", "has_purifier"),
        ):
            switches[key] = {
                "name": name,
                "rationale": ["off", "on"],
                "condition": {"eq": [capability, 1]},
                "command": {"single_control": 1},
            }
        switches["follow_body_sense"]["command"]["follow_body_sense_enable"] = 1
        entities[Platform.SELECT] = {
            "female_care": {
                "name": "保湿呵护",
                "condition": {"eq": ["has_female_care", 1]},
                "status_key": "female_care",
                "command": {"single_control": 1},
                "options": {
                    "关闭": {"female_care": 0},
                    "开启（26°C / 60%）": {
                        "female_care": 1,
                        "temperature": 26,
                        "small_temperature": 0,
                        "dehumidity": 60,
                        "airoptimization": "off",
                    },
                },
            },
        }
        result[model] = config
    return {**result, **mappings}
