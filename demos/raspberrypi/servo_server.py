import socket
import time
import logging
import RPi.GPIO as GPIO

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

PORT = 4017

servo_pin = 11
servo_pulse_freq = 50
pos_angle = 0.0
neg_angle = 180.0

GPIO.setmode(GPIO.BOARD)
GPIO.setup(servo_pin, GPIO.OUT)
servo = GPIO.PWM(servo_pin, servo_pulse_freq)
servo.start(0)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind(('', PORT))
    shutdown = False
    while not shutdown:
        s.listen(5)
        logging.info('listen for connections')
        (conn, addr) = s.accept()
        logging.info("connected to client " + addr[0])
        try:
            while True:
                data = conn.recv(1024)
                msg = data.decode('utf-8')
                logging.info("received command: " + msg)
                if msg == "identify":
                    rep = "raspberry py at " + socket.gethostbyname(socket.gethostname())
                elif msg == "rotate positive":
                    servo.ChangeDutyCycle(2 + (pos_angle / 18))
                    time.sleep(0.5)
                    servo.ChangeDutyCycle(0)
                    rep = "ok"
                    logging.info("rotate positive")
                elif msg == "rotate negative":
                    servo.ChangeDutyCycle(2 + (neg_angle / 18))
                    time.sleep(0.5)
                    servo.ChangeDutyCycle(0)
                    rep = "ok"
                    logging.info("rotate negative")
                elif msg == "disconnect":
                    conn.send(b'disconnecting')
                    break
                elif msg == "shutdown":
                    shutdown = True
                    conn.send(b'shutting down')
                    break
                else:
                    rep = "command unknown"
                conn.send(rep.encode('utf-8'))
        except BrokenPipeError:
            logging.info("broken pipe")
except Exception as e:
    s.close()
    servo.stop()
    GPIO.cleanup()
    raise e

logging.info("close socket")
s.close()
servo.stop()
GPIO.cleanup()
