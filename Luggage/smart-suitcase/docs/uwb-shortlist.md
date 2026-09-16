# UWB shortlist

Recorded September 13, 2026 from the prior vendor-documentation review. Prices below are the listings observed during that review, not guaranteed current quotes. No purchase or final selection has been made. Performance has not been validated on our chassis.

## Recommended first experiment

The [Makerfabs MaUWB STM32 AoA Development Kit](https://www.makerfabs.com/mauwb-stm32-aoa-development-kit.html), listed at $69.80, includes anchor and tag, reports distance and angle, and provides STM32 firmware and a desktop demo. This is the recommended initial bench kit, subject to checking current contents and availability.

## Alternatives

| Option | Observed price | Relevance and limitation |
|---|---:|---|
| [Makerfabs Gen2 anchor](https://www.makerfabs.com/mauwb-aoa-gen2-anchor.html) plus [Gen2 tag](https://www.makerfabs.com/mauwb-aoa-gen2-tag.html) | $39.80 + $29.80 | Robot-following reference files available; individual modules require checking power, connectors, and host interface. Gen1 and Gen2 are incompatible. |
| [Qorvo QM33120WDK2](https://www.qorvo.com/products/ek/QM33120WDK2) | $735 via [Crowd Supply](https://www.crowdsupply.com/qorvo/qm33120wdk2-uwb-dev-kit) | Six nodes, one AoA and five non-AoA; broader evaluation capability but more expense and hardware than the first follower needs. |

The [Makerfabs Gen2 4WD following platform](https://www.makerfabs.com/mauwb-aoa-gen2-4wd-auto-following-robot-platform.html), listed at $199.90, is another integration reference. Vendor describes two AoA anchors, encoders, and ToF sensing, with published hardware/firmware. It does not establish 25 lb payload or loaded suitability. We already have a chassis ordered, so initially use its [repository](https://github.com/Makerfabs/MaUWB_AOA-Gen2) as a reference.

The [ordinary Makerfabs ESP32 DW3000 board](https://www.makerfabs.com/esp32-uwb-dw3000.html) in the initial draft is suitable for ranging experiments, but the documented offering does not establish the bearing capability needed for the complete follower. Its demo library also has multi-node scheduling limitations.

## Bench acceptance work

1. Mount the anchor at intended suitcase height and wear the tag.
2. Log range and bearing during straight walks, turns, and body blockage.
3. Measure valid update rate, latency, angular jumps, dropouts, angular coverage, and elevation effects.
4. Test with chassis motors running, then integrate after results support the declared operating envelope.

In this design, the anchor is attached to the moving suitcase; no fixed building installation is required for the relative range/bearing arrangement.
