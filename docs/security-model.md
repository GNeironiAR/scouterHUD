# Security Model

> **"ScouterHUD handles data that can kill people if it's wrong. Security is not a feature — it's a prerequisite."**

---

## Why this document exists

ScouterHUD displays medical vitals, industrial sensor readings, and vehicle data. Tampered data (a false SpO2 reading, a wrong pressure gauge, a fake speed) can cause physical harm. This document defines how ScouterHUD secures communication, authenticates users, and protects sensitive data — both what's implemented today and what's planned.

We publish this openly because security through obscurity doesn't work. If the model is sound, publishing it makes it stronger. If it has holes, we want them found by researchers, not attackers.

---

## Threat model

### What we're protecting

| Asset | Sensitivity | Example |
|-------|------------|---------|
| Device data stream | HIGH | Heart rate, SpO2, blood pressure, RPM, coolant temp |
| Device metadata | MEDIUM | Device IDs, names, types, broker addresses |
| Authentication credentials | HIGH | PINs, tokens, biometric attestations |
| Control commands | HIGH | Navigation, device switching, connection initiation |
| AI chat content | HIGH | May contain health questions, personal context |
| Audit logs | MEDIUM | Who accessed what device, when |

### Who we're protecting against

| Attacker | Capability | Motivation |
|----------|-----------|------------|
| **Curious bystander** | Same WiFi, basic tools | Snooping on what the HUD shows |
| **Network attacker** | Same LAN, packet capture, injection | Stealing medical/industrial data, injecting false readings |
| **Stolen/lost phone** | Physical access to paired phone | Accessing devices without authorization |
| **Malicious app** | Runs on same phone, no root | Intercepting WebSocket traffic, forging biometric claims |
| **Compromised broker** | Controls MQTT broker | Injecting false data into all connected HUDs |

### What we're NOT protecting against (out of scope)

| Threat | Why out of scope |
|--------|-----------------|
| Root/jailbroken phone | If the OS is compromised, all bets are off. Same as any banking/health app. |
| Physical access to Pi Zero | If someone has the Pi, they have the SD card. Full disk encryption is a future consideration. |
| Nation-state attacker | $50 device is not a military target. Focus on practical threats. |
| Denial of service (jamming WiFi/BLE) | Physical-layer attacks require physical countermeasures, not software. |

---

## Current state (v0.4.0) — honest assessment

### What exists

| Control | Status | Notes |
|---------|--------|-------|
| PIN authentication (4-digit) | Implemented | Demo devices only, hardcoded PINs |
| Biometric authentication | Implemented | Client-side only (local_auth), server trusts claim |
| QR-Link URL validation | Basic | Checks `qrlink://` prefix, parses format |
| Auth level per device | Implemented | `open`, `pin`, `token` in QR-Link URL |

### What's missing

| Gap | Severity | Impact |
|-----|----------|--------|
| **No encryption (WebSocket or MQTT)** | CRITICAL | All data and commands travel in plaintext |
| **No phone authentication** | CRITICAL | Any device on the network can control the HUD |
| **Biometric is spoofable** | CRITICAL | Server accepts `"success"` string without proof |
| **No PIN rate limiting** | CRITICAL | 10,000 combinations, brute-force in seconds |
| **Hardcoded demo PINs** | HIGH | Known PINs in public source code |
| **"Accept any PIN" fallback** | HIGH | Unknown devices accept any PIN |
| **No session management** | HIGH | No way to revoke a connected phone |
| **No MQTT broker auth** | HIGH | Anonymous broker connections |
| **Broadcast to all clients** | MEDIUM | All phones see all state changes |
| **No audit logging** | MEDIUM | No record of who did what |

**Bottom line:** The current implementation trusts the local network completely. This is acceptable for development on a private network. It is NOT acceptable for any real deployment, especially medical or industrial.

---

## Target security architecture

### Layer 1: Phone ↔ HUD pairing (trust establishment)

**Goal:** Only authorized phones can control the HUD. Authorization persists across sessions.

**Mechanism: QR-based pairing (one-time)**

```
1. HUD generates a pairing QR code containing:
   - HUD ID (unique, generated at first boot)
   - One-time pairing token (random 32 bytes, displayed as QR)
   - HUD's public key (Ed25519)

2. Phone scans pairing QR:
   - Phone generates its own Ed25519 keypair
   - Phone stores HUD's public key in Android Keystore / iOS Keychain
   - Phone sends its public key to HUD, signed with the pairing token as proof

3. HUD stores phone's public key:
   - Saved to persistent storage (JSON file on SD card)
   - Associated with a human-readable name ("Ger's Pixel 7")
   - Pairing token is invalidated (one-time use)

4. Result:
   - HUD has: list of paired phones (public keys)
   - Phone has: HUD's public key (in secure storage)
   - Both can verify each other's identity cryptographically
```

**Unpairing:** HUD can remove a phone from its paired list (via another paired phone or physical button on the Pi). Phone can forget the HUD from its settings.

---

### Layer 2: Connection authentication (every session)

**Goal:** Every WebSocket connection proves the phone is paired before accepting commands.

**Mechanism: Challenge-response with biometric gate**

```
1. Phone connects to HUD via WebSocket (or BLE)

2. HUD sends challenge:
   { "type": "auth_challenge", "nonce": "<random 32 bytes hex>" }

3. Phone requires biometric to unlock signing key:
   - local_auth prompts fingerprint/FaceID
   - On success, Android Keystore / iOS Keychain releases the private key
   - Phone signs the nonce with its Ed25519 private key

4. Phone sends response:
   { "type": "auth_response", "signature": "<hex>", "phone_id": "<hex>" }

5. HUD verifies:
   - Looks up phone_id in paired phones list
   - Verifies signature against stored public key
   - If valid: connection is authenticated, commands accepted
   - If invalid: connection rejected, event logged

6. Session token issued:
   - HUD generates a session token (random, time-limited: 8 hours)
   - Subsequent messages include session token (no re-signing needed)
   - Token expires → phone must re-authenticate (biometric again)
```

**Key property:** The biometric is not a boolean sent over the wire. The biometric unlocks a cryptographic key stored in hardware-backed secure storage. The HUD never sees the biometric — it sees a valid cryptographic signature that could only have been produced by the paired phone after biometric verification.

---

### Layer 3: Transport encryption

**Goal:** All data in transit is encrypted and authenticated.

**WebSocket (Phone ↔ HUD):**
- TLS 1.3 (WSS) with the HUD's self-signed certificate
- Phone pins the HUD's certificate during pairing (no CA needed)
- Certificate stored in Android Keystore / iOS Keychain

**BLE (future, Phone ↔ HUD):**
- BLE Secure Connections (LE Secure Connections, ECDH key exchange)
- Bonding with MITM protection (numeric comparison during pairing)
- All GATT characteristics encrypted

**MQTT (HUD ↔ Broker):**
- TLS 1.2+ with server certificate validation
- Client certificate authentication where supported
- QR-Link v2 to include `tls=1` flag and certificate fingerprint
- Fallback: username/password auth over TLS

---

### Layer 4: Device authentication (HUD ↔ Device)

**Goal:** The HUD verifies it's connecting to the legitimate device, not a spoofed broker.

**Current auth levels in QR-Link:**

| Level | Current behavior | Target behavior |
|-------|-----------------|-----------------|
| `open` | No auth, connect directly | No auth, but TLS for transport |
| `pin` | 4-digit PIN, hardcoded | PIN stored encrypted on device, rate-limited (5 attempts / 15 min lockout) |
| `token` | In-memory token store | Token in encrypted persistent storage, with expiration |
| `mtls` | Not implemented | Mutual TLS: HUD presents client cert, broker validates |
| `mfa` | Not implemented | PIN + biometric required |

**PIN hardening:**
- Remove hardcoded demo PINs from production code (move to config file)
- Remove "accept any PIN" fallback
- Rate limiting: 5 failed attempts → 15 minute lockout
- PIN stored as bcrypt hash, never plaintext
- Failed attempts logged with timestamp and source

---

### Layer 5: Audit logging

**Goal:** Every security-relevant event is logged persistently for compliance and forensics.

**Events to log:**

| Event | Data logged | Retention |
|-------|------------|-----------|
| Phone paired | Phone ID, name, timestamp | Permanent |
| Phone unpaired | Phone ID, who initiated, timestamp | Permanent |
| Connection authenticated | Phone ID, auth method, timestamp | 90 days |
| Connection rejected | Source IP, reason, timestamp | 90 days |
| Device connected | Device ID, auth level, phone that initiated, timestamp | 90 days |
| Device disconnected | Device ID, reason, timestamp | 90 days |
| PIN attempt (success/fail) | Device ID, success/fail, attempt count, timestamp | 90 days |
| Biometric auth | Phone ID, success/fail, timestamp | 90 days |
| Data access | Device ID, phone ID, duration, timestamp | 90 days (configurable) |

**Storage:**
- SQLite database on the Pi's SD card
- Rotated after 90 days (configurable, HIPAA requires minimum 6 years for medical records — the deploying organization handles long-term archival)
- Exportable as JSON/CSV for compliance audits
- Not encrypted at rest in v1 (full-disk encryption is a future consideration)

**Privacy note:** Audit logs do NOT contain the actual data values (no vitals, no sensor readings). They record WHO accessed WHAT device WHEN, not what they saw.

---

### Layer 6: Data isolation

**Goal:** Each connected phone only sees what it's authorized to see.

**Current problem:** All connected phones receive all broadcasts (state changes, device lists, chat messages).

**Target behavior:**
- Each WebSocket connection has a session with a phone ID
- HUD tracks which phone initiated which device connection
- State broadcasts are scoped: only the controlling phone gets detailed state
- Other paired phones see "HUD in use" but not device-specific data
- AI chat messages are per-session, not broadcast

---

## Implementation roadmap

### Phase S0 — Quick wins (no architecture change)

These can be implemented now, before hardware arrives:

| Fix | Effort | Impact |
|-----|--------|--------|
| Remove "accept any PIN" fallback | 5 min | Eliminates auth bypass for unknown devices |
| Remove hardcoded demo PINs, move to config file | 30 min | No more public passwords |
| Add PIN rate limiting (5 attempts, 15 min lockout) | 1 hour | Stops brute-force |
| Add input validation (URL length, JSON depth, message rate) | 2 hours | Stops DoS via malformed input |
| Add security headers to HTTP responses | 15 min | Stops clickjacking, XSS |

### Phase S1 — Transport encryption

| Task | Depends on |
|------|-----------|
| Generate self-signed TLS cert on first boot | Pi hardware |
| Enable WSS (WebSocket over TLS) | Self-signed cert |
| Pin HUD certificate in Flutter app | WSS working |
| Enable TLS for MQTT connections | Broker config |
| Add `tls` flag to QR-Link v2 | Protocol update |

### Phase S2 — Phone pairing + authentication

| Task | Depends on |
|------|-----------|
| Generate HUD identity (Ed25519 keypair) on first boot | Pi hardware |
| Pairing QR code generation | HUD identity |
| Phone-side key generation + Keystore storage | Flutter app |
| Pairing handshake protocol | Both sides |
| Challenge-response authentication per session | Pairing complete |
| Biometric-gated key access | Challenge-response |
| Session token management | Authentication |

### Phase S3 — Audit + isolation

| Task | Depends on |
|------|-----------|
| SQLite audit log on Pi | Pi hardware |
| Log all auth events | Authentication working |
| Session-scoped broadcasts | Session management |
| Log export (JSON/CSV) | Audit log |
| Retention policy (auto-rotate) | Audit log |

---

## Compliance mapping

ScouterHUD is not a medical device (it displays data, it doesn't diagnose or treat). However, it handles data that may be subject to regulations:

| Regulation | Applies when | ScouterHUD controls |
|-----------|-------------|-------------------|
| **HIPAA** (US) | Displaying PHI (patient vitals) | Encryption in transit (TLS), access controls (pairing + biometric), audit logs (90-day retention), no cloud transmission |
| **GDPR** (EU) | Processing personal health data | Data minimization (display-only, no storage of values), encryption, right to erasure (unpair + delete logs) |
| **IEC 62443** | Industrial control systems | Network segmentation (HUD on isolated VLAN), authentication, audit trail |
| **FDA 21 CFR Part 11** | If used in clinical trials | Audit trail, electronic signatures (biometric), tamper-evident logs |

**Important disclaimer:** ScouterHUD is an open source project, not a certified medical device. Deploying organizations are responsible for their own compliance assessments. This security model provides the technical controls — compliance requires organizational policies, training, and documentation beyond the scope of this project.

---

## Security principles

1. **Zero trust on the network.** Every connection authenticates. Every message is over TLS. The LAN is not a security boundary.

2. **Biometric proves identity, not a string.** The word "success" is not evidence. A cryptographic signature produced by a hardware-backed key that requires biometric to unlock — that's evidence.

3. **The HUD is the authority.** The phone requests, the HUD decides. The phone cannot bypass the HUD's auth checks. If the HUD requires PIN, the phone must provide a valid PIN. If the HUD requires pairing, the phone must be paired.

4. **Log everything, store nothing.** Log WHO accessed WHAT device WHEN. Never log the actual data values. The HUD is a display — it renders data and forgets it. No vitals database, no health records, no sensor history.

5. **Fail closed.** If authentication fails, disconnect. If TLS handshake fails, don't fall back to plaintext. If the audit log is full, stop accepting connections until the operator resolves it.

6. **Defense in depth.** Pairing + TLS + biometric + challenge-response + session tokens + audit logs. Any single layer can fail and the system remains protected by the others.

---

*ScouterHUD is an open source project by Ger. MIT (Software) / CERN-OHL-S v2 (Hardware).*
