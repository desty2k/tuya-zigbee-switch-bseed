#include "hal/system.h"
#include "stub/hal/stub.h"
#include "hal/zigbee.h"
#include "stub/machine_io.h"
#include <stdio.h>
#include <stdlib.h>

/* xorshift32 state; never 0. Deterministic so tests are reproducible. */
static uint32_t random_state = 0x2545F491u;

static uint8_t reset_fault;

void stub_set_reset_fault(uint8_t fault) {
    reset_fault = fault;
}

uint8_t hal_system_reset_fault(void) {
    return reset_fault;
}

void stub_random_seed(uint32_t seed) {
    random_state = seed != 0 ? seed : 0x2545F491u;
}

uint32_t hal_random_u32(void) {
    random_state ^= random_state << 13;
    random_state ^= random_state >> 17;
    random_state ^= random_state << 5;
    return random_state;
}

void hal_system_reset(void) {
    io_log("SYSTEM",
           "System reset requested - performing graceful stub shutdown");
    io_log("SYSTEM",
           "In real hardware, this would trigger a complete system reset");
    io_log("SYSTEM", "Stub application exiting with code 0");
    exit(0);
}

void hal_factory_reset(void) {
    io_log("SYSTEM", "Factory reset requested - performing stub factory reset");
    io_log(
        "SYSTEM",
        "In real hardware, this would clear all non-volatile memory to defaults");

    hal_zigbee_leave_network();
}
