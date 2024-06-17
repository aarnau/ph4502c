#pragma once

#include "esphome/components/sensor/sensor.h"
#include "esphome/components/voltage_sampler/voltage_sampler.h"
#include "esphome/core/component.h"
#include "esphome/core/defines.h"
#include "esphome/core/hal.h"
#include <vector>
#include <set>
#include <string>

#ifdef USE_ESP32
#include <esp_adc_cal.h>
#include "driver/adc.h"
#endif

namespace esphome {
namespace ph4502c {

struct SensorData {
    float voltage;
    float ph;
};

#ifdef USE_ESP32
// clang-format off
#if (ESP_IDF_VERSION_MAJOR == 4 && ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 4, 7)) || \
    (ESP_IDF_VERSION_MAJOR == 5 && \
     ((ESP_IDF_VERSION_MINOR == 0 && ESP_IDF_VERSION_PATCH >= 5) || \
      (ESP_IDF_VERSION_MINOR == 1 && ESP_IDF_VERSION_PATCH >= 3) || \
      (ESP_IDF_VERSION_MINOR >= 2)) \
    )
// clang-format on
static const adc_atten_t ADC_ATTEN_DB_12_COMPAT = ADC_ATTEN_DB_12;
#else
static const adc_atten_t ADC_ATTEN_DB_12_COMPAT = ADC_ATTEN_DB_11;
#endif
#endif  // USE_ESP32

class pH4502c : public sensor::Sensor, public PollingComponent, public voltage_sampler::VoltageSampler {
 public:
#ifdef USE_ESP32
  /// Set the attenuation for this pin. Only available on the ESP32.
  void set_attenuation(adc_atten_t attenuation) { this->attenuation_ = attenuation; }
  void set_channel1(adc1_channel_t channel) {
    this->channel1_ = channel;
    this->channel2_ = ADC2_CHANNEL_MAX;
  }
  void set_channel2(adc2_channel_t channel) {
    this->channel2_ = channel;
    this->channel1_ = ADC1_CHANNEL_MAX;
  }
  void set_autorange(bool autorange) { this->autorange_ = autorange; }
#endif

  /// Update ADC values
  void update() override;
  /// Setup ADC
  void setup() override;
  void dump_config() override;
  /// `HARDWARE_LATE` setup priority
  float get_setup_priority() const override;
  void set_pin(InternalGPIOPin *pin) { this->pin_ = pin; }
  void set_output_raw(bool output_raw) { this->output_raw_ = output_raw; }
  void set_sample_count(uint8_t sample_count);
  float sample() override;
  void set_signal_voltage(const float voltage) { voltage_signal_ = voltage; }
  void set_calibration_values(const std::vector<SensorData>& calibration) { calibration_values_ = calibration; }
  void schedule_read();
  void build_ph_value();

#ifdef USE_ESP8266
  std::string unique_id() override;
#endif

#ifdef USE_RP2040
  void set_is_temperature() { this->is_temperature_ = true; }
#endif

 protected:
  InternalGPIOPin *pin_;
  bool output_raw_{false};
  uint8_t sample_count_{1};
  float voltage_signal_;
  std::vector<SensorData> calibration_values_{};
  float mean_x_ = 0;
  float mean_y_ = 0;
  float m_ = 0; // Pendiente de la línea recta
  float b_ = 0; // Intersección con el eje Y
  float buffer_arr[10];
  float temp;
  float avgval;
  int reading_index_;
  const int num_readings_ = 10;

#ifdef USE_RP2040
  bool is_temperature_{false};
#endif

#ifdef USE_ESP32
  adc_atten_t attenuation_{ADC_ATTEN_DB_0};
  adc1_channel_t channel1_{ADC1_CHANNEL_MAX};
  adc2_channel_t channel2_{ADC2_CHANNEL_MAX};
  bool autorange_{false};
#if ESP_IDF_VERSION_MAJOR >= 5
  esp_adc_cal_characteristics_t cal_characteristics_[SOC_ADC_ATTEN_NUM] = {};
#else
  esp_adc_cal_characteristics_t cal_characteristics_[ADC_ATTEN_MAX] = {};
#endif
#endif
};

}  // namespace adc
}  // namespace esphome
