"""Exact household cloud models, checked against their vendor codecs.

Unknown capabilities remain diagnostic sensors rather than invented controls.
"""
from copy import deepcopy


def sensor(name, **kw):
    return {"name": name, **kw}


def switch(name, **kw):
    return {"name": name, "rationale": ["off", "on"], **kw}


def binary(name, **kw):
    return {"name": name, "rationale": ["off", "on"], **kw}


def exact(mapping, base, model, edit):
    config = deepcopy(mapping[base])
    edit(config)
    return {model: config, **mapping}


def purifier(c):
    c["centralized"] = []  # Never attach a heating setpoint to unrelated controls.
    e = c["entities"]
    keep = {
        "sensor": ["input_temperature_Sensing", "water_consumption", "water_consumption_ml", "life_1", "life_2", "in_tds", "out_tds"],
        "switch": ["power", "sleep", "wash", "drainage", "leak_water_protection"],
        "binary_sensor": ["lack_water", "standby_status"],
        "lock": ["lock"],
    }
    c["entities"] = e = {p: {k: e[p][k] for k in keys} for p, keys in keep.items()}
    e["switch"]["leak_water_protection"]["attribute"] = "leak_water_protect"
    for key, name in [("no_obsolete_water", "鲜水"), ("smart_no_obsolete_water", "智能鲜水"), ("antifreeze", "防冻"), ("buzzer", "提示音")]:
        e["switch"][key] = switch(name)
    # Gesture on/off shares a wire address with its mode; do not overwrite mode 3 with 1.
    for key, name in [("gesture", "手势感应"), ("leaking_protect_status", "漏水保护状态"), ("installed_heating_module", "已安装加热模块"), ("out_water", "正在出水")]:
        e["binary_sensor"][key] = binary(name)
    e["binary_sensor"]["standby_status"]["rationale"] = [0, 1]
    for key, name in [("gesture_mode", "手势模式代码"), ("error", "故障代码")]:
        e["sensor"][key] = sensor(name)
    # The model app, not the generic boiler template, must define writable ranges.
    for key, name in [("quantify_21", "定量一"), ("quantify_22", "定量二"), ("quantify_23", "定量三"), ("gesture_quantify", "手势定量")]:
        e["sensor"][key] = sensor(name, unit_of_measurement="mL")
    e["sensor"]["life_1"]["name"] = "RO滤芯剩余寿命"
    e["sensor"]["life_2"]["name"] = "PCB滤芯剩余寿命"
    for key in ["life_1", "life_2"]:
        e["sensor"][key].pop("device_class", None)  # Filter life is not a battery.
    for key in ["in_tds", "out_tds"]:
        e["sensor"][key].pop("device_class", None)  # WATER means metered water volume.


def dishwasher(c):
    e = c["entities"]
    c["control_keys"] = ["common_down_type", "switch"]
    # Keep existing start-program selector; show idle separately, never send an invented idle program.
    e["select"]["wash_mode"]["status_key"] = "mode"
    e["select"]["wash_mode"]["options"]["待机（停止）"] = {"mode": "neutral_gear", "work_status": "power_off"}
    e["sensor"]["program_status"] = sensor("当前程序", attribute="mode", value_map={"neutral_gear": "待机"})
    e["select"]["air_set_hour"]["options"]["0"] = {"air_set_hour": 0}
    for key in ["wash_stage", "diy_main_wash", "diy_piao_wash", "diy_times"]:
        e["binary_sensor"].pop(key, None)
        e["sensor"][key] = sensor({"wash_stage":"洗涤阶段代码", "diy_main_wash":"自定义主洗参数", "diy_piao_wash":"自定义漂洗参数", "diy_times":"自定义次数"}[key])
    # doorswitch=1 is an open door, not a running appliance.
    e["binary_sensor"]["doorswitch"].update(name="机门", device_class="door")
    e["lock"] = {"lock": {"name": "童锁", "rationale": ["off", "on"]}}
    e["switch"]["beep_control"] = switch("提示音", attribute="switch", state_attribute="beep_control", rationale=[0, 1], command={"common_down_type": 5})
    e["switch"]["knock_sensor_door_action"] = switch("敲击开门", rationale=[False, True], command={"common_down_type": 7, "knock_sensor_on": True})
    for key, name in [("door_auto_open", "自动开门状态"), ("light_strip_on", "灯带"), ("knock_sensor_on", "敲击感应")]:
        e["binary_sensor"][key] = binary(name, rationale=[0, 1])
    for key, name in [("error_code", "故障代码"), ("wash_region", "洗涤区域代码")]:
        e["sensor"][key] = sensor(name)
    e["sensor"]["dry_set_min"] = sensor("烘干设置时长", unit_of_measurement="min", device_class="duration")


def hood(c):
    e = c["entities"]
    c["centralized"] = []
    c["control_keys"] = ["type", "b6_action", "setting"]
    # Existing stove controls are retained; missing b7 telemetry is not proof of no stove.
    for key in ["power", "light", "wisdom_wind"]:
        e["switch"][key]["command"] = {"electronic_control_version": 2, "type": "b6", "b6_action": "control"}
    e["switch"]["light"]["command"].update(b6_action="setting", setting="light")
    e["select"]["gear"]["command"] = {"electronic_control_version": 2, "type": "b6", "b6_action": "control"}
    e["select"].pop("light", None)
    e["select"].pop("wind_pressure", None)  # No write handler in this model codec.
    for key, name, setting in [("air_curtain_switch", "气帘", "air_curtain"), ("linkage", "烟灶联动", "linkage"), ("ai_butler", "智能管家", "multidimensional"), ("smoke_detector", "烟感", "smoke_detector")]:
        e["switch"][key] = switch(name, command={"electronic_control_version": 2, "type": "b6", "b6_action": "setting", "setting": setting})
    e["sensor"]["total_energy_consumption"]["name"] = "估算耗电量"
    for key, name in [("oilbox_remind", "油杯提醒模式"), ("hotclean_remind", "清洁提醒模式"), ("hotclean_stage", "清洁阶段代码"), ("oilcup_position", "油杯位置代码"), ("error_code", "故障代码"), ("work_status_desc", "运行状态")]:
        e["sensor"][key] = sensor(name)
    for key, name in [("remaining_time", "延时关机剩余时间"), ("hotclean_remaining_minutes", "清洁剩余时间")]:
        e["sensor"][key] = sensor(name, unit_of_measurement="min", device_class="duration")


def heater(c):
    e = c["entities"]
    e["sensor"]["gas_lift_percent"].update(attribute="gas_lift_precent", name="燃气提升百分比")
    e["sensor"]["gas_lift_percent"].pop("device_class", None)
    e["sensor"]["error_code"].update(name="故障代码", value_map={"none": "无故障"})
    e["switch"]["bubble"]["rationale"] = [0, 1]
    e["switch"]["bathtub"]["include_current"] = ["bathtub_water_level"]
    for suffix in ["one", "two", "three"]:
        e["switch"]["person_mode_" + suffix]["include_current"] = ["person_tem_" + suffix]
    for key in ["lamp_control1_power", "lamp_control2_power", "lamp_control3_power"]:
        e["switch"].pop(key, None)
    e["select"]["mode"]["options"].pop("bath", None)
    e["select"]["mode"]["options"].pop("mixed", None)
    e["select"].pop("power_level", None)
    e["sensor"]["power_level"] = sensor("功率档位代码")
    for key in ["type_machine", "capacity"]:
        e["select"].pop(key, None)
        e["sensor"][key] = sensor({"type_machine":"机型代码", "capacity":"容量代码"}[key])
    for key, name in [("high_temp_lock", "高温锁"), ("voice_power", "语音")]:
        e["switch"][key] = switch(name)
    for key, name in [("master_beep", "提示音状态"), ("cruise_antifreeze", "巡航防冻"), ("cruise_antifreeze_error", "巡航防冻故障"), ("appoint_master_switch", "预约总开关")]:
        e.setdefault("binary_sensor", {})[key] = binary(name)
    for key, name in [("cold_hold_duration", "零冷水保温时长"), ("cold_conservation_duration", "零冷水节能时长")]:
        e["sensor"][key] = sensor(name, unit_of_measurement="min", device_class="duration")
