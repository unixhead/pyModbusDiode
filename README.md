# pyModbusDiode

This is a proof of concept for transmitting modbus data over a data diode / unidirectional link.

The "North" side reads Modbus/TCP data based on a configuration file and sends over UDP to a "South" side which receives the data and presents it using a local Modbus/TCP server. Clients can read data from the "South" system.

