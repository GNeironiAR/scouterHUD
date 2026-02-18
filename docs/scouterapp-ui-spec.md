# ScouterApp — UI/UX Specification
## Mobile Remote Control (Landscape Mode)

---

## Overview

ScouterApp is the primary input device for the ScouterHUD ecosystem. It replaces the ScouterGauntlet for most users, providing full remote control of the HUD via smartphone in **landscape orientation**, optimized for **one-handed use**.

The app uses a **gesture-based panel system** with 4 states accessible from a single screen. No navigation menus, no page transitions — everything lives in one view with swipeable panels.

---

## Visual Identity

- **Background:** Dark theme (#1a1a2e)
- **Typography:** Monospaced (Courier New / similar)
- **Color coding by function:**
  - 🔴 Red → Cancel / Delete / Destructive actions
  - 🔵 Blue → Home / Navigation anchor
  - 🟡 Yellow → Scan QR / Numpad accent
  - 🟠 Orange → URL Input / Secondary navigation
  - 🟢 Green → Confirm / Send / OK / Enter
  - 🟣 Purple → AI Assistant
  - 🩵 Cyan → Keyboard / Alpha accent
  - ⚪ Gray/Dim → Inactive / Hints

---

## Screen Layout

### Status Bar (top, always visible)

```
┌──────────────────────────────────────────────┐
│ ● CONNECTED        SCOUTERAPP         REMOTE │
└──────────────────────────────────────────────┘
```

- Left: connection status (green dot + label)
- Center: app name
- Right: current mode (REMOTE / NUMPAD / KEYBOARD / AI CHAT)

### Gesture Guide (bottom, always visible)

```
┌──────────────────────────────────────────────┐
│   ◁ SWIPE → NUMPAD  │  TAP EDGES  │  SWIPE ← ALPHA ▷  │
└──────────────────────────────────────────────┘
```

Subtle hint bar showing available gestures. Highlights the active panel's label.

---

## 4 States

### State 1: BASE (Default)

Main control view. D-Pad centered, action buttons to the right, AI chat button below D-Pad.

```
┌──────────────────────────────────────────────────────┐
│ ▕ N                                              A ▏ │
│ ▕ U          ┌───┐                               L ▏ │
│ ▕ M          │ ▲ │          ┌────────┬────────┐  P ▏ │
│ ▕ P    ┌───┬─┼───┼─┬───┐   │ CANCEL │ SCAN QR│  H ▏ │
│ ▕ A    │ ◀ │ │OK │ │ ▶ │   ├────────┼────────┤  A ▏ │
│ ▕ D    └───┴─┼───┼─┴───┘   │  HOME  │URL INP.│    ▏ │
│ ▕            │ ▼ │          ├────────┼────────┤    ▏ │
│ ▕            └───┘          │ NEXT ▶ │ ◀ PREV │    ▏ │
│ ▕        ┌──────────┐      └────────┴────────┘    ▏ │
│ ▕        │ ◆ AI CHAT│                              ▏ │
│ ▕        └──────────┘                              ▏ │
└──────────────────────────────────────────────────────┘
```

- **Left edge:** Thin vertical line hint + "NUMPAD" label (swipe → to open)
- **Right edge:** Thin vertical line hint + "ALPHA" label (swipe ← to open)
- **D-Pad:** 5 buttons in cross layout (▲▼◀▶ + OK center)
- **Action buttons:** 2x3 grid (CANCEL, SCAN QR, HOME, URL INPUT, NEXT, PREV)
- **AI CHAT button:** Below D-Pad, purple accent, opens AI chat state

---

### State 2: NUMPAD (Swipe right from left edge)

Numeric keypad slides in from the left. D-Pad remains visible at center. Action buttons compact to a single column on the right.

```
┌──────────────────────────────────────────────────────┐
│                                              CLOSE ▏ │
│  ┌───┬───┬───┐       ┌───┐           ┌────────┐   ▏ │
│  │ 1 │ 2 │ 3 │       │ ▲ │           │ CANCEL │   ▏ │
│  ├───┼───┼───┤ ┌───┬─┼───┼─┬───┐    ├────────┤   ▏ │
│  │ 4 │ 5 │ 6 │ │ ◀ │ │OK │ │ ▶ │    │  HOME  │   ▏ │
│  ├───┼───┼───┤ └───┴─┼───┼─┴───┘    ├────────┤   ▏ │
│  │ 7 │ 8 │ 9 │       │ ▼ │           │  SCAN  │   ▏ │
│  ├───┼───┼───┤       └───┘           ├────────┤   ▏ │
│  │ ⌫ │ 0 │SND│   ┌──────────┐       │  NAV   │   ▏ │
│  └───┴───┴───┘   │ ◆ AI CHAT│       └────────┘   ▏ │
│                   └──────────┘                     ▏ │
└──────────────────────────────────────────────────────┘
```

- **Numpad:** 4x3 grid (1-9, ⌫ red, 0, SEND green)
- **D-Pad + AI button:** Shifted right but still accessible
- **Action buttons:** Compact single column (smaller labels)
- **Right edge hint:** "CLOSE" label — swipe ← to return to base
- **Dismiss:** Swipe left or tap outside numpad area

---

### State 3: ALPHA (Swipe left from right edge)

QWERTY keyboard slides in from the right. Vertical SPACE bar on the left side of the keyboard, ENTER on the right. Optimized for one-handed thumb typing.

```
┌──────────────────────────────────────────────────────┐
│ ▕ CLOSE                                              │
│ ▕  ┌────────┐                                        │
│ ▕  │ CANCEL │  ┌───┐  ┌─┐ Q W E R T Y U I O P ┌──┐ │
│ ▕  ├────────┤  │ ▲ │  │S│                       │  │ │
│ ▕  │  HOME  │┌─┼───┼─┐│P│ A S D F G H J K L   │ E│ │
│ ▕  ├────────┤│◀│OK │▶││A│                       │ N│ │
│ ▕  │  SCAN  │└─┼───┼─┘│C│ Z X C V B N M ⌫     │ T│ │
│ ▕  ├────────┤  │ ▼ │  │E│                       │ E│ │
│ ▕  │  NAV   │  └───┘  │ │                       │ R│ │
│ ▕  └────────┘  AI CHT ├─┤                       │  │ │
│ ▕                      │⇧│                       └──┘ │
└──────────────────────────────────────────────────────┘
```

**Keyboard layout detail:**

```
┌──────┐  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐  ┌──────┐
│      │  │ Q │ W │ E │ R │ T │ Y │ U │ I │ O │ P │  │      │
│      │  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘  │      │
│      │    ┌───┬───┬───┬───┬───┬───┬───┬───┬───┐    │      │
│ SPACE│    │ A │ S │ D │ F │ G │ H │ J │ K │ L │    │ENTER │
│      │    └───┴───┴───┴───┴───┴───┴───┴───┴───┘    │      │
│      │      ┌───┬───┬───┬───┬───┬───┬───┬─────┐    │      │
│      │      │ Z │ X │ C │ V │ B │ N │ M │  ⌫  │    │      │
├──────┤      └───┴───┴───┴───┴───┴───┴───┴─────┘    └──────┘
│  ⇧   │
└──────┘
```

- **Left column:** SPACE (tall, full keyboard height) + SHIFT below it
- **Center:** 3 rows QWERTY standard + Backspace (⌫) at end of row 3
- **Right column:** ENTER (tall, full keyboard height)
- **No number row** — keep it simple for text input
- **Dismiss:** Swipe right or tap outside keyboard area

---

### State 4: AI CHAT (Tap ◆ AI CHAT button)

Full-screen conversational interface with the LLM assistant. Replaces all other controls temporarily.

```
┌──────────────────────────────────────────────────────┐
│                 ◆ AI ASSISTANT              ✕ CLOSE  │
│ ─────────────────────────────────────────────────── │
│                                                      │
│                          ┌─────────────────────────┐ │
│                          │ Show engine RPM          │ │
│                          └─────────────────────────┘ │
│  ┌──────────────────────────────┐                    │
│  │ Displaying RPM gauge on HUD.│                    │
│  │ Current: 2,450 RPM          │                    │
│  └──────────────────────────────┘                    │
│                          ┌─────────────────────────┐ │
│                          │ Add coolant temp         │ │
│                          └─────────────────────────┘ │
│  ┌──────────────────────────────┐                    │
│  │ Added coolant temperature.  │                    │
│  │ 87°C — normal range.        │                    │
│  └──────────────────────────────┘                    │
│ ─────────────────────────────────────────────────── │
│  ┌──────────────────────────────────────┐ ┌────────┐ │
│  │ Type command...                      │ │  SEND  │ │
│  └──────────────────────────────────────┘ └────────┘ │
└──────────────────────────────────────────────────────┘
```

- **Header:** Purple accent title + red CLOSE button (top right)
- **Chat area:** Scrollable message history, user messages right-aligned (purple), AI responses left-aligned (white/gray)
- **Input bar:** Text field + SEND button at bottom
- **Text input:** Uses the native OS keyboard here (standard text conversation)
- **Dismiss:** Tap ✕ CLOSE to return to base state

---

## Gesture & Interaction Map

| Action | Gesture | Result |
|---|---|---|
| Open Numpad | Swipe → from left edge | State 1 → State 2 |
| Close Numpad | Swipe ← from center | State 2 → State 1 |
| Open Keyboard | Swipe ← from right edge | State 1 → State 3 |
| Close Keyboard | Swipe → from center | State 3 → State 1 |
| Open AI Chat | Tap ◆ AI CHAT button | Any state → State 4 |
| Close AI Chat | Tap ✕ CLOSE | State 4 → State 1 |
| D-Pad navigation | Tap directional buttons | Sends command to HUD |
| OK / Select | Tap OK (D-Pad center) | Sends select to HUD |

---

## Design Principles

1. **One-handed operation:** Everything reachable with one thumb in landscape
2. **D-Pad always visible:** Except in AI Chat, the D-Pad is always accessible as navigation anchor
3. **Panels don't stack:** Only one panel open at a time (numpad OR alpha, never both)
4. **Color = function:** Consistent color coding across all states, no ambiguity
5. **No menus:** Zero hamburger menus, zero dropdowns — gestures and direct buttons only
6. **Minimal mode switching:** The user stays in base 90% of the time, panels are temporary
