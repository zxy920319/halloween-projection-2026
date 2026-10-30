# Calibration plan

Calibration is not implemented or validated yet. Before projection use:

- Confirm actual reflective-film optical type and mounting geometry.
- Separately test camera-input mirror, display mirror, and optical reflection
  orientation; never relabel left/right landmarks to conceal an inversion.
- Confirm camera-to-activity-area full-body coverage and practical lighting
  with projection on and off.
- Validate the Unity rig's bind pose and coordinate transforms using synthetic
  poses before involving participants.
- Use external video/LED measurement or documented clock synchronization for
  end-to-end latency; host-local monotonic timestamps alone cannot measure it.

Do not include child imagery in calibration artifacts or commit diagnostic
images. Record actual site measurements in `SITE_SURVEY.md`.
