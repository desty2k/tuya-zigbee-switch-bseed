#ifndef _NETWORK_INDICATOR_H_
#define _NETWORK_INDICATOR_H_

#include "indicator_feedback.h"
#include <stdbool.h>

/*
 * Shows network state on the dedicated status LED, or on the relay
 * indicators of a board without one. While not joined the indicators blink
 * 500/500 ms, except a dedicated LED with steady_when_not_connected, which
 * keeps manual_state_when_connected.
 */
typedef struct {
    indicator_feedback_t *indicators[4];
    bool                  has_dedicated_led;
    /* Dedicated LED level while joined. */
    bool                  manual_state_when_connected;
    bool                  steady_when_not_connected;
    bool                  connected;
} network_indicator_t;

void network_indicator_connected(network_indicator_t *indicator);
void network_indicator_not_connected(network_indicator_t *indicator);

/** Applies changed manual_state_when_connected / steady_when_not_connected
 * in the current network state. */
void network_indicator_refresh(network_indicator_t *indicator);

/** Marks the network joined and plays the 7 x 500/500 ms join blink, after
 * which the indicators return to their joined state. */
void network_indicator_commission_success(network_indicator_t *indicator);

#endif
