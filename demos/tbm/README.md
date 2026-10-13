## TBM: Thermal Brood Mover
The thermal brood mover is a manipulative in which the floor of the ant arena is covered with Peltier heaters. It is intended to create spots with (un-) favorable thermal conditions for the brood to study the colony reaction to the change of conditions.
This is a minimal example that just connects to the thermo electric controllers (TECs) of the setup, which regulate the current in the Peltier elements to achieve a set point in temperature. It then reports the temperature and commands it to a new set point, if it is above a certain threshold. More elaborate scenarios are imaginable, where the controllers are turned on on a certain spot in response to events detected in the tracking or temperature data.

## Prerequisites
The TBM setup uses TEC controllers from [Meerstetter Engineering GmbH](https://www.meerstetter.ch/) which can be controlled using the [pyMeCom library](https://github.com/spomjaksilp/pyMeCom). Installation instructions can be found on the git repository.


