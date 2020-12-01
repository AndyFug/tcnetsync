# tcnetsync (Timecode Network Synchronisation)
This library (in its early stages) is intended to provide tools for SMPTE timecode sync across a LAN/WAN/Wifi etc.  The library provides server and client modules with respective classes in each.  Synchronisation relies on hosts having network time synchronisation (e.g. NTP or PTP etc).  Ideally we should build in some type of OS interrogation to check NTP sync status etc.

## Servers
Currently only an MTCServer class is provided.  This server listens to MTC (midi timecode) and shares it with tcnetsync clients.

## Client
The tcnetsync client requests sync from a tcnetsync server.
