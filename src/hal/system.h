#ifndef _HAL_SYSTEM_H_
#define _HAL_SYSTEM_H_

#include <stdint.h>

/**
 * Reset the system/microcontroller
 */
void __attribute__((noreturn)) hal_system_reset(void);

void hal_factory_reset(void);

/** Pseudo-random value for timing jitter; not for security use. */
uint32_t hal_random_u32(void);

/**
 * Zigbee stack fault that reset the device right before this boot: 0 when the
 * previous reset was not a stack fault, otherwise the platform's fault code
 * plus 1 (Telink: the SDK `SYS_EXCEPTTION_*` event). Constant after boot.
 */
uint8_t hal_system_reset_fault(void);

#endif /* _HAL_SYSTEM_H_ */
