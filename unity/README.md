# Unity scaffold (M4)

Copy `Assets/Scripts` into a Unity LTS project (2022.3+; uses `System.Net.WebSockets`, no extra packages).

Scene setup:
1. Create three empty GameObjects (`Skeleton0..2`) and add `Tracking/SkeletonDrawer` to each. Assign a simple unlit material (e.g. Sprites/Default) to `lineMaterial`.
2. Create an empty `Tracking` object, add `SkeletonPool`, and assign the three skeleton roots.
3. Add `PoseReceiver` (assign the pool) and `PoseWebSocketClient` (assign the receiver) to the same or another object.
4. Run the desktop with `python -m desktop.main --host 0.0.0.0 --port 8765 --pose`, then press Play. The client connects to `ws://127.0.0.1:8766/poses`.

Status: NOT_TESTED in Unity (no Unity editor was available when written). Bone lines are a placeholder; Humanoid retargeting of a rigged skeleton model is a later step. See `../docs/UNITY_SETUP.md`.
