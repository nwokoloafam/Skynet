# Home Lab Projects — Master Reference

> **Purpose of this doc:** This is the single source of truth for two related-but-separate projects. Any AI assistant helping with these projects should read this file first. Keep it updated as decisions are made — append, don't delete history; mark superseded decisions instead of erasing them.

**Owner background:** Hardware EE, comfortable with electronics/circuits, new to software/firmware development. Prefers to learn concepts while building, so explanations should include the "why," not just commands to copy-paste.

**Last updated:** 2026-06-24

---

## Project 1: Raspberry Pi 5 Home Server

### Goal
General-purpose home server to learn on. Two concrete use cases to start:
1. **File storage (NAS)** — shared storage accessible from other devices on the home network.
2. **Home automation hub** — for *other* future projects (not the alarm system, at least initially). Likely candidate: Home Assistant.

### Status
🔲 Not yet started — hardware/OS not yet chosen or installed.

### Current Plan / Decisions
| Decision | Choice | Rationale | Status |
|---|---|---|---|
| OS | Raspberry Pi OS Lite (64-bit) or Ubuntu Server 24.04 LTS | Lightweight, headless, well-documented | Open — needs final pick |
| File sharing | Samba (Windows/Mac/Linux compatible) and/or NFS | Samba is easiest cross-platform starting point | Tentative |
| App isolation | Docker + Docker Compose | Lets automation apps (Home Assistant, etc.) be added/removed without touching base OS | Tentative |
| Automation platform | Home Assistant (containerized) | Most common, huge community, integrates with almost anything later | Tentative |
| Remote access | TBD (Tailscale likely candidate) | Needed if accessing server outside home network | Not decided |

### Open Questions
- Storage hardware: USB SSD vs HDD vs NAS HAT? (Not yet specified by owner)
- Static IP / DHCP reservation for the Pi 5 on the home network?
- Backup strategy for the file storage (not yet discussed)

### Hardware Inventory
- Raspberry Pi 5 (RAM size/storage not yet specified — confirm before OS install)
- (Storage media — TBD)

---

## Project 2: Distributed Alarm Clock System

### Goal
A buzzer alarm in the bedroom that can be silenced/snoozed/acknowledged from button modules placed around the apartment — so the user has to physically get up and walk to a button to stop the alarm (classic "get out of bed" alarm clock hack).

### Architecture
```
[Button Module] --HC-12 RF--\
[Button Module] --HC-12 RF---+--> [Bedroom Module: Pi 2W + Buzzer + HC-12]
[Button Module] --HC-12 RF--/
```
- **Bedroom module**: Raspberry Pi 2W — runs the alarm logic, drives the buzzer, listens for HC-12 messages from button modules.
- **Button modules** (qty TBD, "a few," spread across apartment): Seeed XIAO RP2040 + HC-12, each with a physical button. Sends a signal to bedroom module when pressed.
- **Communication**: HC-12 RF transceiver modules (one per node) — long-range, simple serial-based wireless link.

### Status
✅ Hardware selected, PCBs designed for both module types.
🔲 PCBs not yet fabricated/assembled (assume not yet — confirm/update once boards arrive).
🔲 Firmware not yet written.

This is the **first priority project** per the owner — starting hardware → firmware → integration, in that order.

### Hardware Inventory
| Component | Qty | Notes |
|---|---|---|
| Raspberry Pi 2W | 1 | Bedroom module — runs alarm logic + buzzer driver |
| Seeed XIAO RP2040 (mfg # 102010428) | 4 total button nodes planned | Button modules, battery powered |
| HC-12 RF transceiver | 1 per module (Pi 2W + each XIAO) | Inter-module comms |
| Buzzer | 1 (3 buzzer outputs on bedroom module — see pinout) | Bedroom module alarm sound |
| Buttons | 1 per button module | Physical input, active-low (grounded when pressed) |
| Battery (button modules) | TBD chemistry/capacity | Voltage sensed via resistor divider — see pinout |

### Node Count / Range (confirmed)
- **5 nodes total**: 1 bedroom module (Pi 2W) + 4 button modules (XIAO RP2040). **Confirmed.**
- **Max distance**: 6 meters (longest button-to-bedroom path) — well within stock HC-12 antenna range even indoors with walls; no need for high-gain antennas.
- **Battery**: Button modules run on 5V battery supply. Divider is 2x 1MΩ (1:2 ratio) → at full 5V battery, P26 ADC sense pin sees ~2.5V, which is within typical 3.3V-logic ADC range on RP2040. Firmware should multiply sensed ADC voltage x2 to get actual battery voltage. **Confirmed.**

### Confirmed Pinouts

**Bedroom Module (Raspberry Pi 2W)** — ⚠️ **UNRESOLVED / NEEDS OWNER CLARIFICATION**

Owner gave two conflicting pinout statements across messages:
- First pass: GPIO 14 → HC-12 RXD, GPIO 15 → HC-12 TXD, GPIO 18 → HC-12 SET, GPIO 8/7/1 → Buzzer 1/2/3.
- Second pass: "buzzer GPIO 10, 11, and 31. buzzer is GPIO 15 and 16, SET is GPIO 1." (Note: GPIO 31 is not a valid BCM GPIO on Pi 2W's 40-pin header — max accessible BCM GPIO is ~27. Also unclear whether numbers given are BCM GPIO numbers or physical header pin numbers — these are two different schemes and a common source of wiring errors.)

**Do not wire or write firmware against either version until owner provides one final, internally-consistent pinout**, ideally pulled directly from the PCB design files (schematic/netlist) rather than retyped from memory, specifying clearly:
- Numbering scheme used (BCM GPIO # vs physical pin #)
- HC-12: RXD, TXD, SET — 3 pins
- Buzzer: confirm whether there are really 3 separate buzzer channels or 1 buzzer + other functions

Until resolved, treat the Pi 2W bedroom module pinout as **not finalized**.

**Button Module (Seeed XIAO RP2040)**:
| XIAO Pin | Connects to | Function |
|---|---|---|
| D7 | HC-12 (radio RX side) | XIAO TX → HC-12 RX |
| P0 | HC-12 (radio TX side) | XIAO RX ← HC-12 TX |
| P28 | HC-12 SET | Command/transparent mode select |
| P26 | Battery sense | Analog in; resistor divider from battery V+ — 2x 1MΩ resistors (so divider ratio is 1:2, i.e. ADC sees half of battery voltage) |
| P27 | Button | Digital in; active-low — pin reads LOW when button is pressed (grounded), needs internal or external pull-up |

> Note: "5V VDD" mentioned for the battery divider reference — clarify whether this means the battery nominal voltage is ~5V (e.g., 2x 18650 in some config, or a boosted rail) or if 5V is just the divider's top reference rail fed from elsewhere. This affects the actual battery voltage math the firmware needs to do. **Confirm battery chemistry/voltage range before writing the battery-sense code** (e.g., LiPo single-cell is ~3.0-4.2V, would not normally be called "5V").

### Key Technical Decisions
| Decision | Choice | Rationale | Status |
|---|---|---|---|
| Firmware language (XIAO RP2040) | Arduino (C/C++) | Most tutorials/community support, good fit coming from HW background | **Decided** |
| Bedroom module language (Pi 2W) | Python (likely) | Pi 2W runs full Linux, Python has best HC-12/serial + GPIO library support | Tentative |
| Integration with Pi 5 server | None for now | Keep standalone while learning; revisit once both systems are stable | **Decided (for now)** |
| HC-12 channel/frequency plan | TBD | Must assign distinct channels or use addressing so modules don't collide | **Not yet decided — needed before wiring multiple buttons** |
| HC-12 baud rate / air rate | TBD (default 9600 baud serial / 5000bps air rate is a safe starting point) | Defaults are usually fine for small alarm-trigger packets | Tentative |
| Power per button module | TBD | Battery vs wall power affects sleep/wake firmware design | Not decided |

### Open Questions
- How many button modules total, and roughly how far from the bedroom module (affects HC-12 antenna/power needs)?
- Should button modules sleep between presses to save battery, or stay powered all the time (depends on power answer above)?
- Snooze vs full-dismiss logic — does any button stop the alarm, or does it need a specific sequence?
- Do all button modules behave identically, or do we want distinct IDs (e.g., to log which button was pressed)?

### Build Order (per owner's stated priority)
1. **Hardware setup** — wire up one bedroom module (Pi 2W + buzzer + HC-12) and one button module (XIAO RP2040 + button + HC-12) as a proof of concept pair.
2. **Firmware** — get basic HC-12 send/receive working between the two, then add buzzer control and button-triggered dismiss logic.
3. **Scale out** — replicate button module for remaining locations, handle multi-node addressing.
4. **(Later, optional)** — integrate with Pi 5 server / Home Assistant.

---

## Conventions for AI Agents Working on This Project
- This doc should be treated as living memory across sessions/accounts. When a decision is made or changed, update the relevant table row rather than just answering in chat.
- The owner is an EE, new to firmware/software — prioritize explaining *why* a tool/library/pattern is used, not just providing code.
- Don't assume integration between Project 1 and Project 2 unless explicitly stated — they are intentionally decoupled for now.
- Mark items "Decided" only when the owner has explicitly confirmed; otherwise use "Tentative" or "Open Question."
