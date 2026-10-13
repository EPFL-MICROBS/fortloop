## Raspberry Pi servo motor demo
In this demo, a Raspberry Pi is used to steer a sevo motor, for example to open and close a door, based on a condition of a frame, for example an ant that enters the entrance perimeter.

### Software components:

#### servo_server.py
The server script that must be running on a raspberry pi with known IP. sockets must be installed:
```sudo apt-get install socket```
but no other prerequisits. The servo PWM is connected on PIN 11.

#### test_client.py
This program allows to check the connection to the Raspberry Pi. Call:
```python test_client.py xxx.xxx.xxx.xxx```
with the knwon IP of the Raspberry Pi and wait until the connection is established and promps for a command. "identify" + Enter should return an message from the raspberry Pi with its IP.

#### run_servo_hook.py
The real example, starting two hooks, one for display and one for the Raspberry servo controller and runnin in simulation mode. When the green colored individual crosses the border of the small rectangle, the door is opened. When it leaves it, it will be closed again.

