import machine
import time
import rp2

from lib.tplink_lightbulb import TPLinkLightbulb

import network
import socket
import json

### CONFIG ###

## Web server
server_web = True
server_web_port = 80
## Lightbulb
ip_address = 'IP_ADDRESS_OF_LIGHTBULB_HERE'
## Access Point (station)
ssid = 'SSID_HERE'
key = 'KEY_HERE'

### END ###


### LED ###

led = machine.Pin('LED', machine.Pin.OUT)

'''
LED status codes:
-- Light switch
- 2, false = light on
- 3, false = light off
-- Light status
- 2, true = light on
- 3, true = light off
-- Brightness
- 4, false = 50%
- 5, false = 100%
- 6, false = light must turned on to set brightness
-- Reconnect to network
- 1, false = initiating connection
- 2, false = end of connection setup
-- Reset
- 7, false = hard reset
-- All
- 4, true = error with general network access
- 5, true = error while sending action
- 6, true = error while connecting to access point
'''

def led_flash(amount = 1, hold = False):
    delay = 0.1
    if hold:
        delay = 0.2
        
    for i in range(amount):
        if i > 0:
            time.sleep(delay)
        led.on()
        time.sleep(delay)
        led.off()

### END ###


### NETWORKING ###

def network_connect():
    led_flash(1)

    nic = network.WLAN(network.STA_IF)
    nic.active(True)

    nic.config(pm=network.WLAN.PM_PERFORMANCE)

    nic.connect(ssid, key)

    max_wait = 10
    while max_wait > 0:
        if nic.status() < 0 or nic.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(3)

    '''
    Possible nic.status() values:
    -3 = CYW43_LINK_BADAUTH
    -2 = CYW43_LINK_NONET
    -1 = CYW43_LINK_FAIL
    0 = CYW43_LINK_DOWN
    1 = CYW43_LINK_JOIN
    2 = CYW43_LINK_NOIP
    3 = CYW43_LINK_UP
    '''

    if nic.status() != 3:
        print('Failed to connect: {0}'.format(nic.status()))
        # -1 status can come up at times
        led_flash(6, True)
    else:
        print('Connected')
        status = nic.ifconfig()
        print('IP: {0}'.format(status[0]))

    print("Connected to network: {0}".format(nic.isconnected()))
    print("IFCONFIG: {0}".format(str(nic.ifconfig())))
    led_flash(2)

### END ###


### TPLINK LIGHTBULB INIT ###

tpl_light = TPLinkLightbulb(ip_address)

def light_brightness_toggle():
    action_result = None
    brightness_level = tpl_light.sysinfo()
    
    if brightness_level is not None:
            if 'system' not in brightness_level: return
            if 'get_sysinfo' not in brightness_level['system']: return
            if 'light_state' not in brightness_level['system']['get_sysinfo']: return
            if 'brightness' not in brightness_level['system']['get_sysinfo']['light_state']:
                print('Light must be on to apply brightness changes')
                led_flash(6)
                return action_result
                
            key_brightness = brightness_level['system']['get_sysinfo']['light_state']['brightness']
            
            if key_brightness == 50:
                action = tpl_light.brightness(100)
                if action is not None:
                    led_flash(5)
                    action_result = True
                else:
                    led_flash(5, True)
            else:
                action = tpl_light.brightness(50)
                if action is not None:
                    led_flash(4)
                    action_result = False
                else:
                    led_flash(5, True)
    else:
        led_flash(5, True)
    
    return action_result
    
def light_switch():
    print('Getting current light state...')
    switch_new_state = None
    state = tpl_light.switch_state()
    
    if state:
        print('Turning light off...')
        action = tpl_light.switch(False)
        if action is not None:
            switch_new_state = False
            led_flash(3)
        else:
            led_flash(5, True)
    elif state == False:
        print('Turning light on...')
        action = tpl_light.switch(True)
        if action is not None:
            switch_new_state = True
            led_flash(2)
        else:
            led_flash(5, True)
    elif state == None:
        print('Light switch timeout')
        led_flash(5, True)
        
    return switch_new_state
        
def light_state():
    state = tpl_light.switch_state()
    
    if state:
        print('Light is on')
        led_flash(2, True)
    elif state == False:
        print('Light is off')
        led_flash(3, True)
    elif state == None:
        print('Light state timeout')
        led_flash(5, True)
        
    return state
        

### END ###

# Initialize variables to store press time and button state
press_time = 0
button_pressed = False
action_running = False

# Initialize the timer variable
timer = None

# Function to initialize the timer
def start_timer():
    global timer
    timer = machine.Timer()
    timer.init(period=50, mode=machine.Timer.PERIODIC, callback=check_bootsel_button)

# Function to deinitialize the timer
def stop_timer():
    global timer
    if timer is not None:
        timer.deinit()
        
def button_actions(time, button_released = True):
    global action_running
    action_running = True
    
    '''
    Action list

    0 - 500 ms (release) = toggle power
    550 - 1000 ms (release) = power state
    1050 - 3000 ms (release) = toggle between brightness 50% and 100%
    3050 - 5000 ms (release) = reconnect to network
    5050+ ms (hold) = hard reset -- release button while LED flashes to reset, or it will go into UF2 bootloader
    '''
    
    if time >= 5050 and button_released == False:
        led_flash(7)
        machine.reset()
    elif time >= 3050 and time <= 5000 and button_released:
        network_connect()
    elif time >= 1050 and time <= 3000 and button_released:
        light_brightness_toggle()
    elif time >= 550 and time <= 1000 and button_released:
        light_state()
    elif time >= 0 and time <= 500 and button_released:
        light_switch()
    
    action_running = False

# Check BOOTSEL button state
def check_bootsel_button(timer):
    global press_time, button_pressed, action_running
    
    if action_running: return

    if rp2.bootsel_button():
        # BOOTSEL button pressed
        if not button_pressed:
            # If it was not already pressed
            press_time = time.ticks_ms()
            button_pressed = True
        # Calculate and print the hold duration
        hold_duration = time.ticks_diff(time.ticks_ms(), press_time)
        print("BOOTSEL button held for:", hold_duration, "ms")
        button_actions(hold_duration, False)
    else:
        # BOOTSEL button released
        if button_pressed:
            # If it was previously pressed
            hold_duration = time.ticks_diff(time.ticks_ms(), press_time)
            print("BOOTSEL button was held for:", hold_duration, "ms")
            button_pressed = False
            button_actions(hold_duration)

### WEB SERVER ###

def web_server():
    response = ""
    
    addr = socket.getaddrinfo('0.0.0.0', server_web_port)[0][-1]
    
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    
    print('Listening on', addr)
    
    # Listen for connections
    while True:
        try:
            cl, addr = s.accept()
            print('Client connected from: {0}'.format(addr))
            request = cl.recv(1024)
            print(request)
            
            json_response = False
            
            response = "Invalid request -- refer to documentation"
    
            request = str(request)
            light_toggle = request.find('/light/toggle')
            brightness_toggle = request.find('/light/brightness/toggle')
            system_info = request.find('/light/details')

            if light_toggle == 6:
                state = light_switch()
                if state:
                    response = "On"
                elif state == False:
                    response = "Off"
                else:
                    response = "Error"
                    
            if brightness_toggle == 6:
                state = light_brightness_toggle()
                if state:
                    response = "100%"
                elif state == False:
                    response = "50%"
                else:
                    response = "Error"
    
            if system_info == 6:
                system_info = tpl_light.sysinfo()
    
                if system_info is not None:
                    response = system_info["system"]["get_sysinfo"]
                    json_response = True
                else:
                    response = "Error"
                
            if json_response:
                response = json.dumps(response, separators=(",", ":"))
                response = str(response)
                content_type = 'application/json; charset=utf-8'
            else:
                content_type = 'text/html'
                
            response_headers = [
                'HTTP/1.1 200 OK',
                'Content-Type: {0}'.format(content_type),
                'Content-Length: {0}'.format(len(response)),
                'Connection: keep-alive',
                'Keep-Alive: timeout=5'
            ]
    
            cl.send('{0}\r\n\r\n'.format('\r\n'.join(response_headers)))
            cl.send(response)
            cl.close()
    
        except OSError as e:
            cl.close()
            print('Connection closed')

### END ###

def main():
    network_connect()
    
    led_flash(3)
    start_timer()
    
    if server_web:
        web_server()

    while True:
        time.sleep(1)  # Sleep to reduce CPU usage
    
if __name__ == '__main__':
    main()
