# Troubleshooting Guide

> Complete guide for diagnosing and fixing issues with the Water Meter + Leak Detection system (ESP32 → ESP-NOW → Firebase → Next.js).

---

## 1. ESP32 Hardware Issues

### No Power / No Lights

| Cause | Check | Fix |
|-------|-------|-----|
| USB cable is charge-only | Try a known good data cable | Use cable rated for data transfer |
| Wrong USB port | Device Manager → Ports | Use USB 2.0 or 3.0 port directly on computer |
| ESP32 damaged | Check 3.3V pin with multimeter | Replace ESP32 |
| Expansion board short | Check for solder bridges | Remove expansion board, test ESP32 alone |

### No Serial Output

| Cause | Check | Fix |
|-------|-------|-----|
| Wrong COM port | Device Manager → Ports | Select correct COM port |
| Baud rate mismatch | Set to 921600 | In Serial Monitor, set baud to 921600 |
| Driver missing | Device Manager → yellow exclamation | Install [CP210x](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) or CH340 driver |
| Board not in flash mode | Hold BOOT → press EN → release BOOT | Hold BOOT → press EN → release BOOT → Upload |

### ESP32 Crashes / Reboot Loops

```cpp
// Add this to setup() to diagnose
Serial.println("Free heap: " + String(ESP.getFreeHeap()));
Serial.println("Reset reason: " + String(esp_reset_reason()));
```

| Symptom | Cause | Fix |
|---------|-------|-----|
| Brownout detector triggered | Unstable power supply | Use ≥2A adapter, add 1000µF capacitor |
| Guru Meditation Error | Stack overflow / memory issue | Reduce buffer sizes, add `yield()` in loops |
| Watchdog reset | Task blocking > 5 seconds | Add `delay(0)` or `yield()` |
| WiFi disconnect loop | Weak signal | Move router closer, add antenna |
| Flash corruption | Power loss during write | Use `SPIFFS.format()` in setup |

---

## 2. Flow Sensor Issues

### No Pulse Reading

| Cause | Check | Fix |
|-------|-------|-----|
| Wrong GPIO pin | Verify `SENSOR_PINS[]` in config.h | Match config to actual wiring |
| Loose connection | Inspect connections | Push firmly or re-seat |
| Sensor not powered | Measure VCC pin | Should be 4.5V–5V |
| Arrow wrong direction | Arrow on sensor body | Install with flow direction |
| Air trapped | Bubbles in sensor chamber | Tap sensor, purge air |
| Debounce too high | Pulses < 5ms apart missed | Reduce `DEBOUNCE_MS` to 3 |
| Flow too slow | Minimum ~0.5 L/min | Increase flow rate |

**Quick test:** Connect sensor OUT directly to 3.3V momentarily. If Serial Monitor shows pulses, ESP32 is OK — problem is sensor or water flow.

### Wrong Volume Readings

| Symptom | Likely K-factor | Fix |
|---------|----------------|-----|
| Reading too high (overcounts) | PPL too low | Increase `PULSE_PER_LITER` |
| Reading too low (undercounts) | PPL too high | Decrease `PULSE_PER_LITER` |
| Inconsistent readings | Air / turbulent flow | Add straight pipe before sensor |
| Drifts over time | Temperature change | Re-calibrate seasonally |

### Fixture Balance Error

```
Inlet balance = Inlet volume - (Fixture 1 + 2 + 3)
Normal: balance < 10% of inlet
```

| Balance | Meaning | Action |
|---------|---------|--------|
| < 10% | Normal | No action needed |
| 10–20% | Leak suspected | Investigate fixtures |
| > 20% | Hidden leak or sensor fault | Check all connections |

---

## 3. USB Serial Issues

### ESP32 Not Detected on Computer

```bash
# Check if device appears
ls /dev/ttyUSB*
ls /dev/ttyACM*

# Check kernel messages
dmesg | grep -i usb
```

| Issue | Fix |
|-------|-----|
| No `/dev/ttyUSB*` | Use data cable, not charge-only |
| Permission denied | `sudo usermod -a -G dialout $USER && newgrp dialout` |
| Wrong VID:PID | Check `lsusb` — should show `10c4:ea60` (CP2102) or `1a86:7523` (CH340) |
| Multiple devices | Use udev rule for persistent `/dev/ttyESP32` symlink |

### Serial Connection Drops

```python
# Test connection
python3 -c "
from serial_port import find_esp32_port, get_serial_connection
port = find_esp32_port()
print(f'Port: {port}')
ser = get_serial_connection()
print('Connected!')
for _ in range(3):
    print(ser.readline().decode().strip())
"
```

| Symptom | Cause | Fix |
|---------|-------|-----|
| Random disconnects | Loose USB cable | Secure cable, use strain relief |
| `SerialException` on read | ESP32 reset | Handle reconnect in reader (auto-reconnect built-in) |
| Garbage characters | Baud mismatch | Both sides must use **921600** |
| Partial JSON lines | Buffer fragmentation | Reader accumulates until newline (built-in) |

### udev Rule Not Working

```bash
# Check rule
cat /etc/udev/rules.d/99-esp32.rules

# Test rule
udevadm test /dev/ttyUSB0

# Reload
sudo udevadm control --reload-rules
sudo udevadm trigger

# Verify symlink
ls -la /dev/ttyESP32
```

---

## 4. Dashboard / Firebase Issues

| Cause | Check | Fix |
|-------|-------|-----|
| Vercel deployment failed | Check Vercel dashboard → Deployments | Redeploy from Git |
| Firebase config wrong | Check `.env.local` in Next.js project | Verify API key, database URL |
| Firebase Auth not enabled | Firebase Console → Authentication | Enable Email/Password + Google |
| RTDB rules blocking | Firebase Console → Realtime Database → Rules | Set read/write to true for testing |

---

## 5. Plumbing / Mechanical Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Water hammer | Fast valve closing | Install water hammer arrestor |
| Sensor not spinning | Debris in turbine | Remove and clean with soft brush |
| Check valve stuck | Debris or hard water | Disassemble and clean |
| Leaks at threads | Insufficient Teflon tape | Re-wrap with 3–5 turns PTFE tape |
| PPE joint leak | Insufficient heat fusion | Re-weld with PPR welding machine, ensure proper temperature (260°C) |

---

## 6. Diagnostic Commands (Serial Monitor)

Connect ESP32 via USB, open Serial Monitor at **921600 baud**, send:

| Command | Response | Use Case |
|---------|----------|----------|
| `status` | All sensor readings + device state | Quick health check |
| `sensors` | Raw pulse counts per sensor | Debug ISR issues |
| `config` | Current configuration | Verify settings |
| `wifi` | WiFi status + IP + RSSI | Network troubleshooting |

| `calibrate` | Start calibration mode | For bucket test |
| `reset` | Reboot ESP32 | Quick restart |
| `format` | Format SPIFFS storage | Clear corrupted data |
| `heap` | Free heap memory | Check for memory leaks |
| `uptime` | Device uptime in seconds | Know when last rebooted |

---

## 7. Built-in LED Indicator Reference

| LED Pattern | Meaning |
|-------------|---------|
| Solid green | Normal operation, all OK |
| Blink green (1s) | WiFi connecting |
| Blink blue (fast) | Transmitting serial data |
| Solid yellow | Minor leak detected (alert) |
| Solid red | Major leak detected (critical) |
| Red flash | Emergency — urgent action needed |
| Blink white (3x + pause) | Successful data send |
| Blink red (5x + pause) | Send failed / error |
| Off | Deep sleep or no power |

---

## 8. Checklist Before Panicking

- [ ] Is ESP32 getting power? (LED on?)
- [ ] Is USB cable a **data cable**? (not charge-only)
- [ ] Is Serial Monitor baud set to **921600**?
- [ ] Is the flow sensor arrow pointing **WITH** water flow?
- [ ] Are WiFi SSID and password correct?
- [ ] Is `PULSE_PER_LITER` calibrated for each sensor?

---

## 9. RFID Reader (MFRC522) Issues

### Card Not Detected

| Cause | Check | Fix |
|-------|-------|-----|
| Wrong SPI pins | Verify SDA→GPIO 5, SCK→18, MOSI→23, MISO→19, RST→27 | Match config.h to wiring |
| 3.3V not 5V | MFRC522 runs on 3.3V | Connect VCC to 3.3V, NOT 5V (will damage module) |
| Loose SPI wires | Reseat all 7 wires | Use shorter wires, check solder joints |
| Wrong card type | Card must be Mifare Classic 1K/4K | Check card type with RFID phone app |
| Antenna interference | Metal near reader | Mount reader away from metal surfaces |

### RFID Session Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Card valid but no water | SSR not turning ON | Check PIN_SSR in config.h, verify SSR wiring |
| Water starts but stops immediately | Session timeout too short | Increase SESSION_TIMEOUT_MS in config.h |
| Can't end session | Card tap not detected | Ensure card tap triggers endSession() in firmware |
| Session stays on forever | Timeout not implemented | Add SESSION_TIMEOUT_MS logic to local_rules.h |

### Card Reads Unreliably

| Cause | Fix |
|-------|-----|
| Distance too far | Tap card directly on reader (0–3 cm) |
| Multiple readers crosstalk | Shield readers with aluminum foil, increase distance between rooms |
| SPI clock too fast | Add `SPI.setFrequency(1000000)` in setup |

---

## 10. SSR + Solenoid Valve Issues

### Solenoid Does Not Open

| Cause | Check | Fix |
|-------|-------|-----|
| SSR not firing | Measure GPIO 25 with multimeter (should go HIGH) | Check firmware — PIN_SSR must be defined |
| SSR wiring wrong | Verify CTRL→GPIO 25, VCC→5V, GND→GND | Rewire per block-diagram.md |
| Solenoid polarity | DC solenoid has + and - | Swap wires if needed |
| Insufficient current | 40A SSR can handle it, but check 12V PSU | Ensure PSU provides ≥ 1A for solenoid |
| SSR defective | Test SSR with multimeter (output side) | Replace SSR |

### Solenoid Does Not Close (Shutoff Fails)

| Cause | Check | Fix |
|-------|-------|-----|
| SSR stuck ON | Measure GPIO 25 (should go LOW on leak) | Replace SSR — mechanical welding of contacts |
| Firmware bug | Check local leak rules trigger shutoff | Debug with Serial Monitor |
| NC solenoid wrong type | Must be NC (normally closed) | Replace with NC solenoid — NO type will fail-open |
| Power loss = open | NC solenoid closes on power loss (safe) | Verify solenoid is NC type |

### Solenoid Buzzing / Vibrating

| Cause | Fix |
|-------|-----|
| SSR PWM not clean | Ensure GPIO is solid HIGH/LOW, not PWM |
| Low voltage | Check 12V PSU under load |
| Mechanical wear | Replace solenoid |

---

## 11. Getting Help

If stuck:
1. Check ESP32 Serial Monitor at 921600 baud
2. Run the diagnostic commands above
3. Open GitHub Issue with:
   - Serial Monitor output (last 50 lines)
   - Your `config.h` (remove WiFi passwords!)
   - Sensor types and plumbing layout