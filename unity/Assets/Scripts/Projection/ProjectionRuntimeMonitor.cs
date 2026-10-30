using UnityEngine;

namespace Projection
{
    public sealed class ProjectionRuntimeMonitor : MonoBehaviour
    {
        [SerializeField] private PoseReceiver poseReceiver;
        [SerializeField] private PoseWebSocketClient poseClient;
        [SerializeField, Min(1f)] private float heartbeatIntervalSeconds = 5f;
        [SerializeField, Min(0.5f)] private float stalePoseWarningSeconds = 3f;

        private float nextHeartbeatTime;
        private int lastLoggedFrameCount;
        private bool hasLoggedConnectionState;
        private bool lastConnectionState;
        private bool stalePoseWarningLogged;

        private void Awake()
        {
            if (poseReceiver == null)
            {
                poseReceiver = FindObjectOfType<PoseReceiver>();
            }
            if (poseClient == null)
            {
                poseClient = FindObjectOfType<PoseWebSocketClient>();
            }
            if (poseReceiver == null)
            {
                Debug.LogWarning("Projection runtime monitor has no PoseReceiver; frame health is unavailable.", this);
            }
            if (poseClient == null)
            {
                Debug.LogWarning("Projection runtime monitor has no PoseWebSocketClient; connection health is unavailable.", this);
            }
            nextHeartbeatTime = Time.unscaledTime + heartbeatIntervalSeconds;
        }

        private void Update()
        {
            bool connected = poseClient != null && poseClient.IsConnected;
            if (!hasLoggedConnectionState || connected != lastConnectionState)
            {
                Debug.Log($"Pose WebSocket connection: {(connected ? "connected" : "disconnected")}.", this);
                lastConnectionState = connected;
                hasLoggedConnectionState = true;
            }

            bool poseIsStale = poseReceiver != null && poseReceiver.AcceptedFrames > 0 &&
                Time.realtimeSinceStartup - poseReceiver.LastAcceptedRealtime > stalePoseWarningSeconds;
            if (poseIsStale && !stalePoseWarningLogged)
            {
                Debug.LogWarning(
                    $"Pose feed is stale: no accepted frame for " +
                    $"{Time.realtimeSinceStartup - poseReceiver.LastAcceptedRealtime:F1}s.", this);
            }
            stalePoseWarningLogged = poseIsStale;

            if (Time.unscaledTime >= nextHeartbeatTime)
            {
                EmitHeartbeat();
                nextHeartbeatTime = Time.unscaledTime + heartbeatIntervalSeconds;
            }
        }

        public void EmitHeartbeat()
        {
            int acceptedFrames = poseReceiver != null ? poseReceiver.AcceptedFrames : 0;
            long frameId = poseReceiver != null ? poseReceiver.LastFrameId : -1;
            float frameAge = poseReceiver != null && acceptedFrames > 0
                ? Time.realtimeSinceStartup - poseReceiver.LastAcceptedRealtime
                : -1f;
            int frameDelta = acceptedFrames - lastLoggedFrameCount;
            lastLoggedFrameCount = acceptedFrames;
            string ageText = frameAge >= 0f ? $"{frameAge:F2}s" : "unavailable";
            Debug.Log(
                $"Projection heartbeat: socket={(poseClient != null && poseClient.IsConnected ? "up" : "down")}, " +
                $"accepted_frames={acceptedFrames}, frames_last_interval={frameDelta}, " +
                $"last_frame_id={frameId}, pose_age={ageText}.", this);
        }
    }
}
