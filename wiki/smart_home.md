# Smart Home

## Overview
Tuya/SmartLife compatible devices control — lights, fans, AC via voice.

## Supported Devices
Configured in `devices.json`:

| ID | Name | Room | Type |
|----|------|------|------|
| bedroom_light | Bedroom Light | bedroom | light |
| hall_light | Hall Light | hall | light |
| bedroom_fan | Bedroom Fan | bedroom | fan |
| hall_fan | Hall Fan | hall | fan |

## Voice Commands
| Command | Tag |
|---------|-----|
| "Bedroom light off karo" | `[DEVICE: bedroom_light, OFF]` |
| "Hall fan on" | `[DEVICE: hall_fan, ON]` |
| "Sab lights band karo" | Multiple `[DEVICE: ...]` tags |
| "Good night" | All lights + fans OFF |
| "Good morning" | Bedroom light ON |

## Setup (Wipro/SmartLife devices)

### Step 1: Hardware
Buy Tuya/SmartLife compatible switches (Wipro, Orient, Syska)

### Step 2: SmartLife App
Set up devices in SmartLife app (WiFi connect)

### Step 3: Tuya IoT Platform
1. Go to iot.tuya.com → Sign up
2. "Cloud" → "Create Project" → Region: India
3. "Devices" → "Link Tuya App Account" → SmartLife link
4. Copy Access ID + Secret

### Step 4: Config
Add to environment variables:
```
TUYA_ACCESS_ID=your_access_id
TUYA_ACCESS_SECRET=your_secret
```

### Step 5: Device IDs
Add `tuya_id` to each device in `devices.json`:
```json
{
    "id": "bedroom_light",
    "name": "Bedroom Light",
    "room": "bedroom",
    "type": "light",
    "tuya_id": "xxx_from_tuya_dashboard"
}
```

## Technical
- Uses `tuya-connector-python` SDK
- Region: India (`in`)
- API: `https://openapi.tuyain.com`
- Command: `switch_1` with value true/false

## Files
- `smart_home.py` — Tuya device controller
- `devices.json` — Device registry
- `configs/smart_home_config.json` — (same as devices.json)
