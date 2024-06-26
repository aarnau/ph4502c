import logging

import esphome.codegen as cg
import esphome.config_validation as cv
import esphome.final_validate as fv
from esphome.core import CORE
from esphome.components import sensor, voltage_sampler
from esphome.components.esp32 import get_esp32_variant
from esphome.const import (
    CONF_ATTENUATION,
    CONF_ID,
    CONF_NUMBER,
    CONF_PIN,
    CONF_RAW,
    CONF_WIFI,
    DEVICE_CLASS_VOLTAGE,
    STATE_CLASS_MEASUREMENT,
    UNIT_VOLT,
)
from . import (
    ATTENUATION_MODES,
    ESP32_VARIANT_ADC1_PIN_TO_CHANNEL,
    ESP32_VARIANT_ADC2_PIN_TO_CHANNEL,
    ph4502c_ns,
    validate_adc_pin,
)

_LOGGER = logging.getLogger(__name__)

AUTO_LOAD = ["voltage_sampler"]

CONF_SAMPLES = "samples"
CONF_CALIBRATION_VALUES = "calibration_values"
CONF_SIGNAL_VOLTAGE = "signal_voltage"

_attenuation = cv.enum(ATTENUATION_MODES, lower=True)


def validate_config(config):
    if config[CONF_RAW] and config.get(CONF_ATTENUATION, None) == "auto":
        raise cv.Invalid("Automatic attenuation cannot be used when raw output is set")

    if config.get(CONF_ATTENUATION, None) == "auto" and config.get(CONF_SAMPLES, 1) > 1:
        raise cv.Invalid(
            "Automatic attenuation cannot be used when multisampling is set"
        )
    if config.get(CONF_ATTENUATION) == "11db":
        _LOGGER.warning(
            "`attenuation: 11db` is deprecated, use `attenuation: 12db` instead"
        )
        # Alter value here so `config` command prints the recommended change
        config[CONF_ATTENUATION] = _attenuation("12db")

    return config


def final_validate_config(config):
    if CORE.is_esp32:
        variant = get_esp32_variant()
        if (
            CONF_WIFI in fv.full_config.get()
            and config[CONF_PIN][CONF_NUMBER]
            in ESP32_VARIANT_ADC2_PIN_TO_CHANNEL[variant]
        ):
            raise cv.Invalid(
                f"{variant} doesn't support ADC on this pin when Wi-Fi is configured"
            )

    return config


pH4502c = ph4502c_ns.class_(
    "pH4502c", sensor.Sensor, cg.PollingComponent, voltage_sampler.VoltageSampler
)

object_schema = cv.Schema({
    cv.Required('voltage'): cv.float_,
    cv.Required('ph'): cv.float_,
})

CONFIG_SCHEMA = cv.All(
    sensor.sensor_schema(
        pH4502c,
        unit_of_measurement=UNIT_VOLT,
        accuracy_decimals=2,
        device_class=DEVICE_CLASS_VOLTAGE,
        state_class=STATE_CLASS_MEASUREMENT,
    )
    .extend(
        {
            cv.Required(CONF_CALIBRATION_VALUES): cv.All(cv.ensure_list(object_schema)),
            cv.Optional(CONF_SIGNAL_VOLTAGE, default=3.0): cv.float_,
            cv.Required(CONF_PIN): validate_adc_pin,
            cv.Optional(CONF_RAW, default=False): cv.boolean,
            cv.SplitDefault(CONF_ATTENUATION, esp32="0db"): cv.All(
                cv.only_on_esp32, _attenuation
            ),
            cv.Optional(CONF_SAMPLES, default=1): cv.int_range(min=1, max=255),
        }
    )
    .extend(cv.polling_component_schema("60s")),
    validate_config,
)

FINAL_VALIDATE_SCHEMA = final_validate_config


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await sensor.register_sensor(var, config)

    if config[CONF_PIN] == "VCC":
        cg.add_define("USE_ADC_SENSOR_VCC")
    elif config[CONF_PIN] == "TEMPERATURE":
        cg.add(var.set_is_temperature())
    else:
        pin = await cg.gpio_pin_expression(config[CONF_PIN])
        cg.add(var.set_pin(pin))

    cg.add(var.set_output_raw(config[CONF_RAW]))
    cg.add(var.set_sample_count(config[CONF_SAMPLES]))

    if attenuation := config.get(CONF_ATTENUATION):
        if attenuation == "auto":
            cg.add(var.set_autorange(cg.global_ns.true))
        else:
            cg.add(var.set_attenuation(attenuation))

    if CORE.is_esp32:
        variant = get_esp32_variant()
        pin_num = config[CONF_PIN][CONF_NUMBER]
        if (
            variant in ESP32_VARIANT_ADC1_PIN_TO_CHANNEL
            and pin_num in ESP32_VARIANT_ADC1_PIN_TO_CHANNEL[variant]
        ):
            chan = ESP32_VARIANT_ADC1_PIN_TO_CHANNEL[variant][pin_num]
            cg.add(var.set_channel1(chan))
        elif (
            variant in ESP32_VARIANT_ADC2_PIN_TO_CHANNEL
            and pin_num in ESP32_VARIANT_ADC2_PIN_TO_CHANNEL[variant]
        ):
            chan = ESP32_VARIANT_ADC2_PIN_TO_CHANNEL[variant][pin_num]
            cg.add(var.set_channel2(chan))

    # Convert calibration values
    calibration_values = []
    for value in config[CONF_CALIBRATION_VALUES]:
        calibration_value = cg.StructInitializer(
            ph4502c_ns.struct("SensorData"),
            ("voltage", value["voltage"]),
            ("ph", value["ph"]),
        )
        calibration_values.append(calibration_value)

    cg.add(var.set_calibration_values(calibration_values))

    cg.add(var.set_signal_voltage(config[CONF_SIGNAL_VOLTAGE]))