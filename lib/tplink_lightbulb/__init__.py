import socket
import json

class TPLinkLightbulb:
    
    def __init__(self, ip_address):
        self.ip_address = ip_address
        
    @classmethod
    # Encrypt request
    def encrypt(self, buffer, key = 0xAB):
        for i in range(len(buffer)):
            c = buffer[i]
            buffer[i] = c ^ key
            key = buffer[i]
    
        return buffer

    # Decrypt response
    def decrypt(self, buffer, key = 0xAB):
        for i in range(len(buffer)):
            c = buffer[i]
            buffer[i] = c ^ key
            key = c
    
        return buffer

    # Send request to target device and recieve response
    def send(self, request_json):
        result = None
    
        request_json_data = json.dumps(request_json, separators=(",", ":"))
        server_address = (self.ip_address, 9999)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(5)

        # Create a UDP socket
        try:
            # Send data
            print(bytearray(str(request_json_data).encode('utf-8')))
            message = bytes(self.encrypt(bytearray(str(request_json_data).encode('utf-8'))))
            print(f'Sending: {message}')
            s.sendto(message, server_address)

            # Receive response
            print('Waiting for response...')
            data, server = s.recvfrom(4096)
            print(data)
            result = self.decrypt(bytearray(data))
            result = bytes(result)
            result = json.loads(result)

            print(f'Received: {result}')
        except OSError:
            print('Connection timed out -- no response or wrong hostname')
        finally:
            s.close()
        
        return result
    
    ### Core actions ###
        
    # System information
    def sysinfo(self):
        cmd = {"system": {"get_sysinfo": {} }}
    
        return self.send(cmd)

    # Lighting details
    def details(self):
        cmd = {"smartlife.iot.smartbulb.lightingservice": { "get_light_details": {} }}
    
        return self.send(cmd)

    # Light brightness (only takes effect when light is on)
    def brightness(self, percentage = 50):
        cmd = {"smartlife.iot.smartbulb.lightingservice": { "transition_light_state": {"brightness": percentage, "transition_period": 1,},},}
    
        return self.send(cmd)

    # Light control
    def switch(self, switch_on = True):
        state = 1
        if not switch_on:
            state = 0
    
        cmd = {"smartlife.iot.smartbulb.lightingservice": { "transition_light_state": {"on_off": state, "transition_period": 1,},},}
    
        return self.send(cmd)
    
    ### Actions utilising above actions ###
    
    # Light control switch status
    def switch_state(self):
        result = None
        data = self.sysinfo()
        print(data)
        if data is not None:
            if 'system' not in data: return result
            if 'get_sysinfo' not in data['system']: return result
            if 'light_state' not in data['system']['get_sysinfo']: return result
            if 'on_off' not in data['system']['get_sysinfo']['light_state']: return result
                
            key_on_off = data['system']['get_sysinfo']['light_state']['on_off']
            if key_on_off == 1:
                result = True
            else:
                result = False
                    
        return result
