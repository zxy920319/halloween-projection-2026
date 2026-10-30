# Troubleshooting

- **`ModuleNotFoundError: websockets` or `PIL`**: activate the intended virtual
  environment and install the repository package as shown in README.
- **Desktop will not bind**: verify the address belongs to the desktop and the
  port is unused. Do not solve this by opening the service to the public Internet.
- **Sender reconnect loop**: confirm receiver is running, both devices are on the
  trusted LAN, URL/port/path are correct, and host firewall allows the Pi source.
- **Protocol close (1002)**: sender and receiver versions may not match, or the
  binary packet is malformed; inspect logs without saving camera imagery.
- **No `/dev/video*`**: run the Pi probe and confirm USB enumeration. Do not
  infer that OpenNI2 will work; Astra Pro Plus/Pi 5 ARM64 remains a hardware gate.
- **Preview window fails**: use `--preview` only on a desktop with Tk available;
  transport can run without preview.
- **Mock frames shown**: these are generated color bars, never camera imagery.
