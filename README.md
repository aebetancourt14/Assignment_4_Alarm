README.md  
# Assignment 4 – Networked Alarm System  
WES 267 – Embedded Systems

## Overview

This project implements a networked alarm system using a server-client architecture running as separate processes on the same machine. The system uses:

- Python multiprocessing
- TCP sockets
- PMODA GPIO output
- A piezo buzzer connected to PMODA D3

The client sends tone commands to the server over a TCP connection.  
The server generates a square wave at the requested frequency to drive the buzzer.

---

## System Architecture

### High-Level Design

+-------------------+        TCP Socket        +-------------------+
|   CLIENT PROCESS  |  <-------------------->  |   SERVER PROCESS  |
|                   |                           |                   |
| - Connect         |                           | - Listen          |
| - Send TONE cmd   |                           | - Parse command   |
| - Disconnect      |                           | - Drive buzzer    |
+-------------------+                           +-------------------+
                                                      |
                                                      v
                                                PMODA D3 GPIO
                                                      |
                                                      v
                                                  Piezo Buzzer

---

## Hardware Configuration

### Board
PYNQ-Z2 (Base Overlay)

### Wiring

| PMODA Pin | Connection |
|------------|------------|
| D3         | Center pin of piezo buzzer (signal) |
| GND        | Other buzzer pin (ground) |

PMOD outputs are 3.3V logic only. Do not use 5V.

---

## Software Design

### 1. Multiprocessing

Two separate processes are created:

- server_proc
- client_proc

Example:

p_server = mp.Process(target=server_proc, args=(stop_evt,))
p_client = mp.Process(target=client_proc, args=(stop_evt,))

---

### 2. Server Behavior

The server:

- Binds to 127.0.0.1:<PORT>
- Remains in listening mode
- Accepts connections
- Receives messages
- Parses commands:
  - TONE <freq> <duration>
  - QUIT

When a tone command is received, the server generates a square wave on PMODA Data pin 3.

---

### 3. Square Wave Tone Generation

The buzzer is driven using alternating HIGH and LOW values at half-period intervals:

write HIGH  
sleep 1/(2*f)  
write LOW  
sleep 1/(2*f)

Implementation:

def play_tone(freq_hz, duration_s=0.5):
    half_period = 1.0 / (2.0 * freq_hz)
    t_end = time.time() + duration_s

    while time.time() < t_end:
        write_buzzer_gpio(1)
        time.sleep(half_period)
        write_buzzer_gpio(0)
        time.sleep(half_period)

    write_buzzer_gpio(0)

This produces a square wave at frequency freq_hz.

---

### 4. Client Behavior

The client:

- Connects to the server
- Sends tone messages
- Optionally disconnects
- Can send QUIT to terminate the system

Example message:

TONE 880 0.5

This plays an 880 Hz tone for 0.5 seconds.

---

## Features Implemented

✔ Multiprocessing (separate server/client processes)  
✔ TCP communication using sockets  
✔ Hardware GPIO output on PMODA  
✔ Square wave tone generation  
✔ Graceful shutdown using event signaling  
✔ Localhost testing (can be adapted to remote IP)

---

## How to Run

### Step 1 – Ensure base overlay is loaded

from pynq.overlays.base import BaseOverlay
base = BaseOverlay("base.bit")

### Step 2 – Run the script

python alarm_system.py

### Step 3 – Use client controls

c  -> connect  
t  -> send tone  
q  -> quit  

---

## Example Use Case

- Button press triggers tone
- Server produces audible alarm
- Client disconnect ends alarm session

This demonstrates:

- Networking concepts
- I/O control
- Concurrent processing
- Embedded hardware interfacing

---

## Learning Outcomes

This assignment demonstrates understanding of:

- TCP socket programming
- Multiprocessing vs threading
- Event synchronization
- Digital signal generation (square wave)
- Hardware interfacing on embedded platforms