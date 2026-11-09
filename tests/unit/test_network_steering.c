#include "base_components/network_steering.h"
#include "hal/system.h"
#include "hal/zigbee.h"
#include "support/fake_clock.h"
#include "support/fake_tasks.h"
#include "support/runner.h"
#include <stdint.h>

static hal_zigbee_network_status_t status;
static uint32_t random_value;
static uint32_t starts;
static uint32_t last_start_ms;
static uint32_t now_ms;

void hal_zigbee_start_network_steering(void) {
    starts++;
    last_start_ms = now_ms;
    status        = HAL_ZIGBEE_NETWORK_JOINING;
}

hal_zigbee_network_status_t hal_zigbee_get_network_status(void) {
    return status;
}

uint32_t hal_random_u32(void) {
    return random_value;
}

static void reset(void) {
    fake_clock_reset();
    fake_tasks_reset();
    status        = HAL_ZIGBEE_NETWORK_NOT_JOINED;
    random_value  = 0;
    starts        = 0;
    last_start_ms = 0;
    now_ms        = 0;
    network_steering_init();
}

static void advance(uint32_t ms) {
    now_ms += ms;
    fake_clock_advance_ms(ms);
    fake_tasks_poll();
}

/* Ends the running attempt without a join and lets the main loop see it. */
static void fail_attempt(void) {
    status = HAL_ZIGBEE_NETWORK_NOT_JOINED;
    network_steering_update(status);
}

TEST(retry_delay_doubles_from_one_second_to_a_thirty_second_cap) {
    const uint32_t bases[] = { 1000, 2000, 4000, 8000, 16000, 30000, 30000 };

    for (uint8_t i = 0; i < sizeof(bases) / sizeof(bases[0]); i++) {
        uint32_t base = bases[i];

        ASSERT_EQ(base * 3 / 4, network_steering_retry_delay_ms(i + 1, 0));
        ASSERT_EQ(base * 5 / 4,
                  network_steering_retry_delay_ms(i + 1, base / 2));
        ASSERT_EQ(base * 3 / 4,
                  network_steering_retry_delay_ms(i + 1, base / 2 + 1));
    }
    ASSERT_EQ(30000 * 5 / 4, network_steering_retry_delay_ms(255, 15000));
}

TEST(retry_delay_stays_within_jitter_for_any_random_value) {
    const uint32_t randoms[] = { 1, 0x7FFFFFFFu, 0x80000000u, 0xFFFFFFFFu,
                                 123456789u };

    for (uint8_t n = 1; n < 10; n++) {
        uint32_t base = network_steering_retry_delay_ms(n, 0) * 4 / 3;

        for (uint8_t r = 0; r < sizeof(randoms) / sizeof(randoms[0]); r++) {
            uint32_t delay = network_steering_retry_delay_ms(n, randoms[r]);

            ASSERT_TRUE(delay >= base * 3 / 4);
            ASSERT_TRUE(delay <= base * 5 / 4);
        }
    }
}

TEST(first_attempt_starts_at_once_and_retries_wait) {
    reset();
    ASSERT_TRUE(!network_steering_update(status));
    ASSERT_EQ(1, starts);
    ASSERT_TRUE(!network_steering_update(status));
    ASSERT_EQ(1, starts);

    fail_attempt();
    for (uint32_t i = 0; i < 749; i++) {
        advance(1);
        network_steering_update(status);
    }
    ASSERT_EQ(1, starts);
    advance(1);
    ASSERT_EQ(2, starts);
    ASSERT_EQ(750, last_start_ms);
    ASSERT_EQ(2, network_steering_attempts());
}

TEST(retries_follow_the_schedule) {
    const uint32_t bases[] = { 1000, 2000, 4000, 8000, 16000, 30000, 30000 };

    reset();
    random_value = 0xFFFFFFFFu;
    network_steering_update(status);
    for (uint8_t i = 0; i < sizeof(bases) / sizeof(bases[0]); i++) {
        uint32_t failed_at = now_ms;
        uint32_t expected  = network_steering_retry_delay_ms(i + 1,
                                                             random_value);

        fail_attempt();
        advance(expected - 1);
        ASSERT_EQ(i + 1u, starts);
        advance(1);
        ASSERT_EQ(i + 2u, starts);
        ASSERT_EQ(failed_at + expected, last_start_ms);
        ASSERT_TRUE(expected >= bases[i] * 3 / 4);
        ASSERT_TRUE(expected <= bases[i] * 5 / 4);
    }
}

TEST(failed_start_counts_as_an_attempt_without_a_join) {
    reset();
    network_steering_update(status);
    status = HAL_ZIGBEE_NETWORK_NOT_JOINED; /* stack refused the start */
    network_steering_update(status);
    ASSERT_EQ(1, starts);
    advance(750);
    ASSERT_EQ(2, starts);
}

TEST(join_reports_steering_and_restarts_the_schedule) {
    reset();
    network_steering_update(status);
    fail_attempt();
    advance(750);
    fail_attempt();
    advance(1500);
    ASSERT_EQ(3, starts);

    status = HAL_ZIGBEE_NETWORK_JOINED;
    ASSERT_TRUE(network_steering_update(status));
    ASSERT_TRUE(!network_steering_update(status));

    status = HAL_ZIGBEE_NETWORK_NOT_JOINED;
    network_steering_update(status);
    ASSERT_EQ(4, starts);
    fail_attempt();
    advance(749);
    ASSERT_EQ(4, starts);
    advance(1);
    ASSERT_EQ(5, starts);
}

TEST(leave_starts_an_attempt_at_once) {
    reset();
    status = HAL_ZIGBEE_NETWORK_JOINED;
    ASSERT_TRUE(!network_steering_update(status));
    ASSERT_EQ(0, starts);

    status = HAL_ZIGBEE_NETWORK_NOT_JOINED;
    network_steering_update(status);
    ASSERT_EQ(1, starts);
}

TEST(boot_joined_and_rejoin_without_steering_do_not_report) {
    reset();
    status = HAL_ZIGBEE_NETWORK_JOINED;
    ASSERT_TRUE(!network_steering_update(status));
    status = HAL_ZIGBEE_NETWORK_JOINING;
    ASSERT_TRUE(!network_steering_update(status));
    status = HAL_ZIGBEE_NETWORK_JOINED;
    ASSERT_TRUE(!network_steering_update(status));
    ASSERT_EQ(0, starts);
}

TEST(restart_cancels_the_wait) {
    reset();
    network_steering_update(status);
    fail_attempt();
    advance(750);
    fail_attempt();
    advance(100);
    ASSERT_EQ(2, starts);

    network_steering_restart();
    network_steering_update(status);
    ASSERT_EQ(3, starts);
    fail_attempt();
    advance(750);
    ASSERT_EQ(4, starts);
}

int main(void) {
    RUN_TEST(retry_delay_doubles_from_one_second_to_a_thirty_second_cap);
    RUN_TEST(retry_delay_stays_within_jitter_for_any_random_value);
    RUN_TEST(first_attempt_starts_at_once_and_retries_wait);
    RUN_TEST(retries_follow_the_schedule);
    RUN_TEST(failed_start_counts_as_an_attempt_without_a_join);
    RUN_TEST(join_reports_steering_and_restarts_the_schedule);
    RUN_TEST(leave_starts_an_attempt_at_once);
    RUN_TEST(boot_joined_and_rejoin_without_steering_do_not_report);
    RUN_TEST(restart_cancels_the_wait);

    return test_runner_failures == 0 ? 0 : 1;
}
