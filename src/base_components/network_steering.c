#include "network_steering.h"

#include "base_components/timer_service.h"
#include "hal/system.h"

#define RETRY_FIRST_DELAY_MS       1000u
#define RETRY_MAX_DELAY_MS         30000u
/* Failed attempts whose delay doubles (1 to 16 s); one more would pass the cap. */
#define RETRY_DOUBLING_FAILURES    5u

static app_timer_t retry_timer;
static bool        status_seen;
static hal_zigbee_network_status_t last_status;
static bool     attempt_active;
static bool     steered_since_join;
static uint8_t  failed_attempts;
static uint32_t attempts;

uint32_t network_steering_retry_delay_ms(uint8_t failures, uint32_t random) {
    uint32_t base = RETRY_MAX_DELAY_MS;

    if (failures <= RETRY_DOUBLING_FAILURES) {
        base = RETRY_FIRST_DELAY_MS << (failures > 0 ? failures - 1u : 0u);
    }
    return base - base / 4u + random % (base / 2u + 1u);
}

static void start_attempt(void) {
    attempts++;
    attempt_active     = true;
    steered_since_join = true;
    hal_zigbee_start_network_steering();
}

static void retry_timer_handler(void *arg) {
    (void)arg;
    if (hal_zigbee_get_network_status() == HAL_ZIGBEE_NETWORK_NOT_JOINED &&
        !attempt_active) {
        start_attempt();
    }
}

void network_steering_init(void) {
    timer_init(&retry_timer, retry_timer_handler, NULL);
    status_seen        = false;
    attempt_active     = false;
    steered_since_join = false;
    failed_attempts    = 0;
    attempts           = 0;
}

void network_steering_restart(void) {
    timer_cancel(&retry_timer);
    attempt_active  = false;
    failed_attempts = 0;
}

bool network_steering_update(hal_zigbee_network_status_t status) {
    bool left = status_seen && last_status == HAL_ZIGBEE_NETWORK_JOINED &&
                status != HAL_ZIGBEE_NETWORK_JOINED;

    status_seen = true;
    last_status = status;
    if (status == HAL_ZIGBEE_NETWORK_JOINED) {
        bool joined_by_steering = steered_since_join;

        steered_since_join = false;
        network_steering_restart();
        return joined_by_steering;
    }
    if (left) {
        network_steering_restart();
    }
    if (status != HAL_ZIGBEE_NETWORK_NOT_JOINED) {
        return false;
    }
    if (attempt_active) {
        attempt_active = false;
        if (failed_attempts < UINT8_MAX) {
            failed_attempts++;
        }
        timer_restart(&retry_timer,
                      network_steering_retry_delay_ms(failed_attempts,
                                                      hal_random_u32()));
    } else if (!timer_is_active(&retry_timer)) {
        start_attempt();
    }
    return false;
}

uint32_t network_steering_attempts(void) {
    return attempts;
}
