#ifndef _NETWORK_STEERING_H_
#define _NETWORK_STEERING_H_

#include "hal/zigbee.h"
#include <stdbool.h>
#include <stdint.h>

/*
 * Starts network steering while the device is not joined. The first attempt
 * starts at once; after each attempt that ends without a join the next one
 * waits 1, 2, 4, 8, 16, then 30 s for every further attempt, each delay
 * jittered by +-25 % so devices powered up together spread their joins. A
 * join, a leave or network_steering_restart() starts over at the immediate
 * attempt.
 */

/** Delay before the next attempt after `failures` (>= 1) consecutive
 * attempts without a join, in ms; `random` is a uniform 32-bit value. */
uint32_t network_steering_retry_delay_ms(uint8_t failures, uint32_t random);

void network_steering_init(void);

/**
 * Main-loop pump with the current network status. Returns true on the pass
 * that sees the network joined after this module started steering since the
 * previous join, so a boot already joined or a rejoin without steering
 * returns false.
 */
bool network_steering_update(hal_zigbee_network_status_t status);

/** Factory reset: the next attempt starts at once. */
void network_steering_restart(void);

/** Steering starts since boot. */
uint32_t network_steering_attempts(void);

#endif
