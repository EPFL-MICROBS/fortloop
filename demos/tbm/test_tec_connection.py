import sys
import logging
from mecom import MeCom, ResponseException  # Meerstetter TEC controller object

logging.getLogger().setLevel(logging.INFO)


def test_connection(port):
    tec = MeCom(serialport=port)
    address = tec.get_parameter(parameter_name="Device Address")
    status = tec.status()
    if status == "Error":
        # Error 143 = "Measured sink temperature too high" (TEC Family User Manual 5216G (FW V5.00))
        n_error = tec.get_parameter(parameter_name="Error Number")
        logging.info("Error number returned: {}".format(n_error))
        # Status returns "3" which according to the pyMeCom code should be an error, but no error is risen upon other calls

    sn = tec.get_parameter(parameter_name="Device Serial Number", address=address)
    logging.info("connected to TEC decive {}, s/n: {}, status: {}".format(address, sn, status))

    temp1 = tec.get_parameter(parameter_name="Object Temperature", address=address, parameter_instance=1)
    temp2 = tec.get_parameter(parameter_name="Object Temperature", address=address, parameter_instance=2)
    logging.info("query for object temperature, measured temperature channel 1: {}C, channel 2: {}C".format(temp1, temp2))


    stable_id = tec.get_parameter(parameter_name="Temperature is Stable", address=address)
    if stable_id == 0:
        stable = "temperature regulation is not active"
    elif stable_id == 1:
        stable = "is not stable"
    elif stable_id == 2:
        stable = "is stable"
    else:
        stable = "state is unknown"
    logging.info("query for loop stability, loop {}".format(stable))


if __name__=="__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Must provide com port")
    for address in sys.argv[1:]:
        test_connection(address)
