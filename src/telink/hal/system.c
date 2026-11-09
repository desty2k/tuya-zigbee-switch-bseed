#include "hal/system.h"
#pragma pack(push, 1)
#include "tl_common.h"
#include "zb_api.h"
#pragma pack(pop)
#include <stdbool.h>
#include <stdint.h>

void hal_system_reset(void) {
    mcu_reset();
    // mcu_reset() does not return but is not declared noreturn.
    for (;;) {
    }
}

void hal_factory_reset(void) {
    zb_factoryReset();
}

uint32_t hal_random_u32(void) {
    return drv_u32Rand();
}

/*
 * The SDK posts a system exception when its MAC, buffer pools, task queue or
 * NWK tables reach a state it cannot recover from, and keeps running unless a
 * handler resets. Without the reset the stack stops sending and forwarding
 * while the main loop still clears the watchdog. The event code survives the
 * reset in DEEP_ANA_REG1, which only a power cycle clears; the SDK uses
 * DEEP_ANA_REG0 and DEEP_ANA_REG2 itself.
 */
#define RESET_FAULT_ANA_REG    DEEP_ANA_REG1

extern volatile u16 T_evtExcept[4];

static uint8_t reset_fault;

static void stack_fault_reset(void) {
    analog_write(RESET_FAULT_ANA_REG, (u8)(T_evtExcept[1] + 1));
    hal_system_reset();
}

void telink_system_init(void) {
    reset_fault = analog_read(RESET_FAULT_ANA_REG);
    analog_write(RESET_FAULT_ANA_REG, 0);
    sys_exceptHandlerRegister(stack_fault_reset);
}

uint8_t hal_system_reset_fault(void) {
    return reset_fault;
}
