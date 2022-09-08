# pyModbusDiode

This is a proof of concept for transmitting modbus data over a data diode / unidirectional link.

The "North" side reads Modbus/TCP data based on a configuration file and sends over UDP to a "South" side which receives the data and presents it using a local Modbus/TCP server. Clients can read data from the "South" system.

This is a POC and should not be used in production, the South Modbus server is not read-only and there may be other bugs.

![overview](https://raw.githubusercontent.com/unixhead/pyModbusDiode/main/pyModbusDiode.drawio.png)
