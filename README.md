
# README

## Introduction

This repository contains the code for an external component of ESPHome that allows the integration of the PH4502C sensor for pH readings in water. The PH4502C sensor board operates at 5 volts, while the ESP32 works at a maximum voltage of 3.3 volts. Therefore, it is crucial to construct a voltage divider before connecting the sensor to the ESP32. This README provides a detailed guide on setting up the sensor, including a wiring diagram, calibration information, and ESPHome configuration examples.

## Voltage Divider Warning

**Important:** The PH4502C sensor board operates at 5 volts, whereas the ESP32 microcontroller supports a maximum voltage of 3.3 volts on its GPIO pins. To safely connect the sensor to the ESP32, a voltage divider must be constructed. Failure to do so may damage the ESP32.

## Sensor Calibration

Proper calibration of the PH4502C sensor is essential for accurate pH readings. Refer to the manufacturer's calibration instructions to perform an initial calibration of the probe. Calibration typically involves using known pH buffer solutions to adjust the sensor's output. Ensure the sensor is calibrated before integrating it with ESPHome.

For detailed calibration instructions, please refer to the [Calibration Guide](https://cdn.awsli.com.br/969/969921/arquivos/ph-sensor-ph-4502c.pdf).

## ESPHome Configuration

To integrate the PH4502C sensor with ESPHome, use the following YAML configuration. This example specifies the analog pin 35, an update interval of 10 seconds, an analog pin attenuation of 11dB, precision to 4 decimal places, and calibration values obtained from controlled measurements.

### Sensor Configuration

```yaml
sensor:
  - platform: ph4502c
    pin: 35
    name: "pH Sensor"
    update_interval: 10s
    attenuation: 11db
    accuracy_decimals: 4
    calibration_values:
      - voltage: 1.52
        ph: 6.86
      - voltage: 1.81
        ph: 4.01
```

- **pin:** Specifies the analog pin used for the sensor.
- **update_interval:** Defines how frequently the sensor readings are updated.
- **attenuation:** Sets the analog pin attenuation.
- **accuracy_decimals:** Determines the number of decimal places for sensor readings.
- **calibration_values:** Lists the calibration values obtained from the sensor using known pH buffer solutions.

### External Components Configuration

To include the external component from this GitHub repository, add the following to your ESPHome configuration:

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/aarnau/ph4502c
      ref: main
    components: [ ph4502c ]
```

This configuration fetches the PH4502C component from the specified GitHub repository.
