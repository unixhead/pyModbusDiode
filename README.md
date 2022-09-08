# pyModbusDiode

This is a proof of concept for transmitting modbus data over a data diode / unidirectional link.

A cheap diode can be obtained using media converters that support single fibre links, such as the Lanode CFT-206XD. An even cheaper solution, but obviously not a true diode, would be a firewall that supports disabling stateful inspection, such as Fortigate with the asymroute configuration.


The "North" side reads Modbus/TCP data based on a configuration file and sends over UDP to a "South" side which receives the data and presents it using a local Modbus/TCP server. Clients can read data from the "South" system.

This is a POC and should not be used in production, the South Modbus server is not read-only and there may be other bugs.

![overview](https://raw.githubusercontent.com/unixhead/pyModbusDiode/main/pyModbusDiode.drawio.png)
