# TPLink LightBulb Pico

Basic controls for TP-Link light bulbs via button or HTTP for RPi Pico W

This software is intended to be used under MicroPython on a Raspberry Pi Pico W. The instructions will assume it would be in use, although it is possible use on other microcontrollers (with modifications depending on what components get used).

The included TPLink-Lightbulb library is a basic port of the [tplink-lightbulb](https://github.com/konsumer/tplink-lightbulb) library that is originally written in JavaScript for use under environments such as 'Node.js'.

## Installation

### MicroPython

Download the latest stable MicroPython UF2 file from https://micropython.org/download/RPI_PICO/ and follow the initial installation instructions there.

Last tested working version: `RPI_PICO_W-20240602-v1.23.0.uf2`

### Uploading MicroPython files

There are a few ways to go about this. The easiest way would be to use Thonny to gain access to MicroPython. The files should then be uploaded to the root directory (`/`).

Pressing the 'run current script' button or re-plugging the device should then have it run the script.. although, it will not work right out of the gate as it will need to be first configured.

## Configuration

There are several parts of the script that will need to be modified in order to get it up and running.

| Variable   | Description                                                                |
| ---------- | -------------------------------------------------------------------------- |
| ip_address | IP address of TP-Link light bulb                                           |
| server_web | Enable or disable HTTP server that the script would be hosting             |
| port       | Port number of the HTTP server                                             |
| ssid       | Name (SSID) of the access point where the light bulb would be reachable on |
| key        | Access point authentication key                                            |

## Usage

This allows for basic controls over:

-   Light toggle
-   Brightness
-   Light state
-   System information (HTTP only)
-   Access point reconnect (self only)
-   Device hard reset (self only)

The controls can be operated either by pressing or press and holding the BOOTSEL button, or through the HTTP server.

Refer to the (block) comments under the main script. This will go into detail when it comes to the different LED patterns and different button actions based on button hold durations. This will also show the different endpoints available.

## Expanding on functionality

The partially ported library used to communicate with the light bulb can do far more. Only what was needed for this project was ported, though. For example, no reboot command was included.

If you need more, feel free to add commands in to your own copy. For reference, the aforementioned JavaScript library has many examples. It could also be used in a normal version of Python.
