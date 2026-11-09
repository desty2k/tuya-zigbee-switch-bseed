#ifndef DEVICE_CONFIG_DEVICE_CONFIG_SERVICE_H_
#define DEVICE_CONFIG_DEVICE_CONFIG_SERVICE_H_

#include "device_config/device_composition.h"
#include "zigbee/management_protocol.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define DEVICE_CONFIG_TEXT_CAPACITY     128
#define DEVICE_CONFIG_SCHEMA_VERSION    1

/* Called when the state changes other than through a request: a lock gesture
 * or a factory reset. */
typedef void (*device_config_change_listener_t)(void);

typedef void (*device_config_led_mode_provider_t)(
    void *context, device_config_led_mode_t mode);

typedef struct {
    uint16_t                 schema_version;
    uint32_t                 revision;
    const char *             config;
    uint16_t                 config_len;
    device_config_status_t   status;
    device_config_error_t    error;
    device_config_led_mode_t led_mode;
    uint8_t                  multi_press_reset;
    uint8_t                  child_lock;
} device_config_service_state_t;

void device_config_service_init(void);
const device_config_service_state_t *device_config_service_get_state(void);
const char *device_config_service_config(void);

/**
 * Checks a candidate config string without storing it. A string the image
 * cannot run sets Status `error` and LastError to the reason (memory only,
 * nothing persisted) and returns that reason. While a restart is pending
 * every candidate is refused with DEVICE_CONFIG_ERROR_PENDING and the state
 * is kept.
 */
device_config_error_t device_config_service_check(const char *config,
                                                  size_t config_len);

/** Checks the candidate, stores it and schedules the restart. */
device_config_error_t device_config_service_apply(const char *config,
                                                  size_t config_len);

/**
 * Sets Status `error` and the LastError that a parser or preflight result
 * means; the boot path and a config write map a result the same way.
 */
device_config_error_t device_config_service_set_parse_error(
    config_parse_result_t result);
void device_config_service_set_led_mode_provider(
    device_config_led_mode_provider_t provider, void *context);
device_config_error_t device_config_service_set_led_mode(uint8_t mode);

/** True for 0 (multi-press reset off) and for 5..10 presses. */
bool device_config_service_multi_press_reset_valid(uint8_t count);
device_config_error_t device_config_service_set_multi_press_reset(uint8_t count);

/** Stores the child lock (0 or 1) and applies it to the local inputs. */
device_config_error_t device_config_service_set_child_lock(uint8_t locked);
void device_config_service_set_change_listener(device_config_change_listener_t listener);

/** Releases and forgets the child lock, then performs the platform factory
 * reset (leave the network). */
void device_config_service_factory_reset(void);
void device_config_service_set_error(device_config_error_t error);

#endif
