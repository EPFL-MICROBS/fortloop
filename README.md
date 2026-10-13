= FORTloop =

Intro.

## Basic example
Running the basic example:

``` python demos/run_blueprint.py```

should print the message `INFO:root:Processing frame at time <epoch>` roughly every two seconds.

## Usage
The source code in the basic example is explained in this paragraph.

The core concept of fort loop is a mother process, called `Loop` which starts an arbitrary number of child processes, called `Hook`. Therefore, each script must import those components:
``` from fortloop import Loop, Hook ```

A custom hook object has the following structure
```
class EmptyHook(Hook):
    def __init__(self, sample_period_sec=0, log_filename=''):
        super().__init__(sample_period_sec)
        self.aggregated = None

    def process_frame(self, frame):
        self.aggregated = frame["positions"]
        if frame["timestamp"] - self.t_prev > self.p_sample:
            self.t_prev = frame["timestamp"]
            logging.info("Processing frame at time {}".format(frame["timestamp"]))
        
    def store(self):
        np.save(self.f_store("empty_hook_state.npy"), self.aggregated)

    def restore(self):
        f_latest = self.latest_state_file("empty_hook_state.npy")
        print(f_latest)
        if f_latest is None:
            self.aggregated = None
        else:
            self.aggregated = np.load(f_latest)

```
* The constructor function `__init__(sample_period_sec=0, log_filename='')` should be used to initialize any containers, like `self.aggregated`, for data aggregation if this is needed. This is not needed if only the actual frame is processed and the past frames are not relevant. The `sample_period_sec` specifies at what frequency actions should be taken. It is recommended to set this to a value which is a bit lower than the tracking period to make sure that heavy code which defines actions does not prevent the tracking queue to be fully consumed before the next action. Failure to do so would cause actions to be taken based on outdated tracking frames.

* The `process_frame(frame)` is called whenever a new frame of tracking data is available. Data aggregation code that should not miss any tracking frames should be placed outside the `if` statement. All potentially slow action code (hardware communication, costly computations on aggregated data) should be implemented inside the `if` statement.

* The `store` and `restore` functions are used to save the internal state of the hook, aggregated data or hardware state for example. The store function is called when the loop is terminated by the user or if an exception ("error") occurs. The user must specify in what form the state should be saved. This can be a csv, json, numpy array as shown, or any other format. If `f_store` is used together with `latest_state_file`, the latest state will be loaded automatically. Note that multiple files with different formats can be used at the same time; the user must make sure to correctly save and load these files.

The the loop can be initialized:
```
example_hook = EmptyHook(sample_period_sec=2)
fortloop = Loop([example_hook], log_folder='')
```
and launched in simulation mode, i.e. reading data from a file:
```
f_hermes = "tracking.0000.hermes"
fortloop.simulate(f_hermes, simulate_period=0.2)
```
or from an actual tracking host:
```
host = "hostname"
fortloop.run(host)
```

## Examples

# TODO:
* Fork pymecom, add serial number command
* add instructions to make usb device available