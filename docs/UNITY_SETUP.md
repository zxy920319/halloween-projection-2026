# Unity integration scaffold

The Unity scripts in this repository define a minimal `persons[]` message and a
track-keyed skeleton pool. They are **not a complete renderer**: no Humanoid
retargeting, IK, WebSocket client dependency, materials, model, or tested
Unity project is included.

1. Create a Unity LTS project using the locally installed supported editor.
2. Copy `unity/Assets/Scripts` into `Assets/Scripts`.
3. Add a scene object with `SkeletonPool`; assign up to three pre-rigged
   skeleton root objects in the Inspector.
4. Integrate an explicitly reviewed Unity-compatible WebSocket client, then
   pass received JSON to `PoseReceiver.ApplyJson`. Do not accept arbitrary
   network connections from outside the local desktop.
5. Add and test rig-specific retargeting only after validating coordinate
   handedness, bind pose, confidence handling, and safe behavior for missing
   landmarks.

Unity Editor compilation and PlayMode/EditMode tests were not available in the
current environment.
