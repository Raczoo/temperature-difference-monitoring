# import required libraries
import network
import socket
import dht
from time import sleep
from secrets import secrets
from machine import Pin
import json

# Pin setup
intled = machine.Pin("LED", machine.Pin.OUT)
sensor = dht.DHT11(Pin(27))
sensor2 = dht.DHT11(Pin(26))

# turn the onboard LED ON to indicate startup
intled.value(1)
# wait for 3 seconds
sleep(3)
# turn the onboard LED OFF
intled.value(0)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# prevent the wireless chip from activating power-saving mode when it is idle
wlan.config(pm=0xa11140)

# set a static IP address for Pico
# your router IP could be very different eg: 192.168.1.1
wlan.ifconfig(('10.10.0.94', '255.255.255.0', '10.10.0.1', '8.8.8.8'))

# enter your wifi "SSID" and "PASSWORD"
wlan.connect(secrets["ssid"], secrets["password"])

# Wait for connect or fail
max_wait = 20
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    sleep(1)

# Handle connection error
if wlan.status() != 3:
    intled.value(0)
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

print('listening on', addr)

while True:
    if wlan.status() == 3:
        intled.value(1)
    else:
        intled.value(0)
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024)
        request = str(request)
        print(request)

        # Get the measurements from the sensor
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()

        # Get the measurements from the second sensor
        sensor2.measure()
        temperature2 = sensor2.temperature()
        humidity2 = sensor2.humidity()

        # Prepare the data as a dictionary
        data = {
            "temp": str(temperature),
            "hum": str(humidity),
            "temp2": str(temperature2),
            "hum2": str(humidity2)
        }

        # Convert the data to a JSON string
        json_data = json.dumps(data)

        # Send headers notifying the receiver that the data is of type JSON for application consumption
        cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')

        # Send the JSON data
        cl.send(json_data)

        # Close the connection
        cl.close()

    except OSError as e:
        print('connection closed')

    # Close the connection
    cl.close()
