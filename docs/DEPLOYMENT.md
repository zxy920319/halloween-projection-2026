# Deployment checklist

Every item below is unverified on real hardware until you record evidence for it
in `VALIDATION_REPORT.md`. Do not mark a step `PASS` without a command and log.

## 1. Pi 5 camera (M2)
- [ ] `bash scripts/pi_probe.sh`; save the output locally (see `CAMERA_COMPATIBILITY.md`).
- [ ] Confirm a V4L2 RGB node streams fresh frames at the target FPS.
- [ ] Mount per `CAMERA_MOUNTING_CHECKLIST.md`; fill in `SITE_SURVEY.md`.

## 2. Desktop
- [ ] `python -m pip install -e ".[dev,pose]"`
- [ ] Place an official MediaPipe `.task` model in `models/` (git-ignored).
- [ ] `python scripts/evaluate_video.py <authorized clip> --max-persons 2` and review
      ID switches / occluded ratio.
- [ ] Register the startup task: `deploy/windows/Register-HalloweenDesktopTask.ps1`
      (bind to the LAN IP; firewall inbound 8765 to the Pi only).

## 3. Pi service
- [ ] Install `deploy/pi/halloween-pi.service` with the desktop IP; check
      `systemctl status` and `journalctl`.
- [ ] If `systemctl status` shows `status=217/USER`, the `User=` in the unit does not
      exist on the Pi. Set it to a real account (`id <user>`), add it to `video`
      (`sudo usermod -aG video <user>`), and fix the `WorkingDirectory`/`ExecStart` paths.
- [ ] `python scripts/check_network.py DESKTOP_LAN_IP --port 8765` from the Pi.

## 4. Unity and projector
- [ ] Open the `ProjectionCalibration` scene; set the projector display.
- [ ] Align with the grid (**C**), set optical mirror (**M**), fullscreen (**F**).

## 5. Acceptance (see `MULTIPERSON_ACCEPTANCE.md`, `PROJECTION_M5.md`)
- [ ] One person, then two, then three only if the camera view covers them.
- [ ] Crossing, occlusion, exit/re-entry; no skeleton mirrors the wrong person.
- [ ] 30-minute continuous run, then a 2-hour on-site run.
- [ ] End-to-end latency measurement (high-speed camera method).

## Safety and privacy
Adult supervision, stable tripod, no glass/film in front of the camera, no
recording or uploading of children's imagery, trusted LAN only (unauthenticated `ws://`).
