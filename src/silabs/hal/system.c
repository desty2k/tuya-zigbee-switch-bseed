#include "hal/system.h"
#include "app/framework/include/af.h"
#include "hal/zigbee.h"
#include "micro-common.h"
#include <stdbool.h>
#include <stdint.h>

void hal_system_reset(void) {
    halReboot();
    // halReboot() does not return but is not declared noreturn.
    for (;;) {
    }
}

void hal_factory_reset(void) {
    hal_zigbee_leave_network();
    sl_zigbee_clear_binding_table();
}

// EmberZNet resets on its own assertions; they are not reported here.
uint8_t hal_system_reset_fault(void) {
    return 0;
}

uint32_t hal_random_u32(void) {
    return ((uint32_t)sl_zigbee_get_pseudo_random_number() << 16) |
           sl_zigbee_get_pseudo_random_number();
}
