#include <Arduino.h>
#include "driver/pcnt.h"

#define QCM_INPUT_PIN 27

#define PCNT_UNIT        PCNT_UNIT_0
#define PCNT_H_LIM_VAL   20000
#define PCNT_L_LIM_VAL  -20000

// 移動窓の設定：100ms × 10個 ＝ 1.0秒間
#define WINDOW_SIZE 10
#define SAMPLE_INTERVAL_MS 100

volatile uint32_t overflow_count = 0;
uint32_t window_buffer[WINDOW_SIZE] = {0};
uint8_t window_index = 0;

static void IRAM_ATTR pcnt_intr_handler(void *arg) {
    uint32_t status = 0;
    pcnt_get_event_status(PCNT_UNIT, &status);
    if (status & PCNT_EVT_H_LIM) {
        overflow_count++;
    }
}

void setup_pcnt() {
    pinMode(QCM_INPUT_PIN, INPUT_PULLDOWN);

    pcnt_config_t pcnt_config = {};
    pcnt_config.pulse_gpio_num = QCM_INPUT_PIN;
    pcnt_config.ctrl_gpio_num = PCNT_PIN_NOT_USED;
    pcnt_config.lctrl_mode = PCNT_MODE_KEEP;
    pcnt_config.hctrl_mode = PCNT_MODE_KEEP;
    pcnt_config.pos_mode = PCNT_COUNT_INC;
    pcnt_config.neg_mode = PCNT_COUNT_DIS;
    pcnt_config.counter_h_lim = PCNT_H_LIM_VAL;
    pcnt_config.counter_l_lim = PCNT_L_LIM_VAL;
    pcnt_config.unit = PCNT_UNIT;
    pcnt_config.channel = PCNT_CHANNEL_0;

    pcnt_unit_config(&pcnt_config);
    pcnt_filter_disable(PCNT_UNIT);
    pcnt_event_enable(PCNT_UNIT, PCNT_EVT_H_LIM);

    pcnt_counter_pause(PCNT_UNIT);
    pcnt_counter_clear(PCNT_UNIT);

    pcnt_isr_service_install(0);
    pcnt_isr_handler_add(PCNT_UNIT, pcnt_intr_handler, NULL);
    pcnt_intr_enable(PCNT_UNIT);

    pcnt_counter_resume(PCNT_UNIT);
}

// 100ms 区間のパルス数を取得
uint32_t read_and_reset_interval_pcnt() {
    int16_t current_count = 0;
    pcnt_get_counter_value(PCNT_UNIT, &current_count);

    uint32_t overflows = overflow_count;
    overflow_count = 0;
    pcnt_counter_clear(PCNT_UNIT);

    if (current_count < 0) current_count = 0;
    return (overflows * PCNT_H_LIM_VAL) + (uint32_t)current_count;
}

unsigned long last_time = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n==========================================");
    Serial.println("  10MHz QCM (10Hz Output / 1s Sliding Window)");
    Serial.println("==========================================");

    setup_pcnt();
    last_time = millis();
}

void loop() {
    unsigned long current_time = millis();
    unsigned long elapsed_ms = current_time - last_time;

    // 100msごとに処理を実行
    if (elapsed_ms >= SAMPLE_INTERVAL_MS) {
        // 1. 直近 100ms のパルス数を取得
        uint32_t interval_pulses = read_and_reset_interval_pcnt();

        // 2. リングバッファを更新
        window_buffer[window_index] = interval_pulses;
        window_index = (window_index + 1) % WINDOW_SIZE;

        // 3. 過去10回分（直近1.0秒間）の総パルス数を合算
        uint32_t total_pulses_1s = 0;
        for (int i = 0; i < WINDOW_SIZE; i++) {
            total_pulses_1s += window_buffer[i];
        }

        // 周波数 (Hz) 換算（直近1秒間の合計パルス数そのもの）
        double frequency = (double)total_pulses_1s;
        double delta_f = frequency - 10000000.0;

        Serial.printf("Pulses: %8u | Freq: %10.2f Hz | Delta_f: %+8.2f Hz\n",
                      total_pulses_1s, frequency, delta_f);

        last_time = current_time;
    }
}