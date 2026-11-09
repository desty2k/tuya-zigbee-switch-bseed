#include "network_indicator.h"
#include <stddef.h>

#define NETWORK_INDICATOR_SLOTS                           \
        (sizeof(((network_indicator_t *)0)->indicators) / \
         sizeof(((network_indicator_t *)0)->indicators[0]))

static bool network_indicator_blinks(const network_indicator_t *indicator) {
    return !indicator->connected &&
           !(indicator->has_dedicated_led &&
             indicator->steady_when_not_connected);
}

void network_indicator_refresh(network_indicator_t *indicator) {
    bool blink = network_indicator_blinks(indicator);

    for (size_t i = 0; i < NETWORK_INDICATOR_SLOTS; i++) {
        indicator_feedback_t *feedback = indicator->indicators[i];

        if (feedback == NULL) {
            break;
        }
        if (blink) {
            indicator_feedback_network_not_connected(feedback);
            continue;
        }
        indicator_feedback_network_connected(feedback);
        if (indicator->has_dedicated_led) {
            indicator_feedback_set_base_state(
                feedback, indicator->manual_state_when_connected);
        }
    }
}

void network_indicator_connected(network_indicator_t *indicator) {
    indicator->connected = true;
    network_indicator_refresh(indicator);
}

void network_indicator_not_connected(network_indicator_t *indicator) {
    indicator->connected = false;
    network_indicator_refresh(indicator);
}

void network_indicator_commission_success(network_indicator_t *indicator) {
    network_indicator_connected(indicator);
    for (size_t i = 0; i < NETWORK_INDICATOR_SLOTS; i++) {
        if (indicator->indicators[i] == NULL) {
            break;
        }
        indicator_feedback_commission_success(indicator->indicators[i]);
    }
}
