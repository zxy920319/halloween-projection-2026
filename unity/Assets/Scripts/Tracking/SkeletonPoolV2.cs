using System;
using UnityEngine;

namespace Tracking
{
    // Version 2: a single skeleton, hidden until a person is tracked, that follows the
    // person's horizontal position on screen while staying at a fixed height.
    public sealed class SkeletonPoolV2 : MonoBehaviour
    {
        [SerializeField] private GameObject skeletonRoot;
        [SerializeField] private Camera screenCamera;
        [SerializeField, Min(0f)] private float edgeMargin = 0.6f;
        [SerializeField] private float xOffset;
        [SerializeField, Min(0.01f)] private float xScale = 1f;
        [SerializeField] private bool invertX;
        [SerializeField, Min(0.01f)] private float smoothTime = 0.12f;
        [SerializeField, Min(0f)] private float lostTimeoutSeconds = 0.75f;
        [SerializeField, Range(0f, 1f)] private float anchorMinVisibility = 0.5f;
        [SerializeField, Range(0f, 1f)] private float actionMinVisibility = 0.6f;
        [SerializeField, Range(0.01f, 1f)] private float raisedHandMargin = 0.12f;

        private string currentTrackId;
        private float lastSeenTime = float.NegativeInfinity;
        private float targetX;
        private float velocityX;
        private bool handRaisedLastFrame;

        public event Action<PoseActionEventArgs> PoseActionDetected;

        public GameObject SkeletonRoot => skeletonRoot;
        public string CurrentTrackId => currentTrackId;
        public bool IsShowing => skeletonRoot != null && skeletonRoot.activeSelf;

        private void Awake()
        {
            if (skeletonRoot != null) skeletonRoot.SetActive(false);
        }

        public void ApplyFrame(PoseFrame frame)
        {
            if (frame == null || frame.persons == null || skeletonRoot == null) return;
            TrackedPerson person = SelectTarget(frame.persons, currentTrackId);
            if (person == null) return;

            lastSeenTime = Time.time;
            if (person.tracking_state != "tracked") return; // occluded: stay frozen in place

            bool firstFrame = currentTrackId != person.track_id || !skeletonRoot.activeSelf;
            currentTrackId = person.track_id;
            if (TryGetAnchorX(person.landmarks, out float normalizedX))
            {
                targetX = HorizontalScreenMapper.Map(normalizedX, frame.mirrored_input, HalfWidth(),
                                                    xOffset, xScale, invertX);
                if (firstFrame)
                {
                    SetX(targetX);
                    velocityX = 0f;
                }
            }
            if (!skeletonRoot.activeSelf) skeletonRoot.SetActive(true);

            var driver = skeletonRoot.GetComponentInChildren<SkeletonPoseDriver>(true);
            if (driver != null) driver.ApplyPose(person.landmarks, frame.mirrored_input);
            bool raised = IsHandRaised(person.landmarks);
            if (raised && !handRaisedLastFrame)
                PoseActionDetected?.Invoke(new PoseActionEventArgs(person.track_id, 0, PoseActionEvent.HandRaised));
            handRaisedLastFrame = raised;
        }

        private void Update()
        {
            if (skeletonRoot == null || !skeletonRoot.activeSelf) return;
            if (Time.time - lastSeenTime > lostTimeoutSeconds)
            {
                Hide();
                return;
            }
            float x = Mathf.SmoothDamp(skeletonRoot.transform.localPosition.x, targetX, ref velocityX, smoothTime);
            SetX(x);
        }

        private void Hide()
        {
            var driver = skeletonRoot.GetComponentInChildren<SkeletonPoseDriver>(true);
            if (driver != null) driver.ClearPose();
            skeletonRoot.SetActive(false);
            currentTrackId = null;
            handRaisedLastFrame = false;
        }

        private void SetX(float x)
        {
            Vector3 p = skeletonRoot.transform.localPosition;
            p.x = x;
            skeletonRoot.transform.localPosition = p;
        }

        // Width of the visible area at the skeleton's depth, minus a margin so it never clips.
        private float HalfWidth()
        {
            Camera cam = screenCamera != null ? screenCamera : Camera.main;
            if (cam == null) return 3f;
            float half;
            if (cam.orthographic) half = cam.orthographicSize * cam.aspect;
            else
            {
                float depth = Mathf.Abs(cam.transform.InverseTransformPoint(skeletonRoot.transform.position).z);
                half = depth * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad) * cam.aspect;
            }
            return Mathf.Max(0f, half - edgeMargin);
        }

        // Prefers the current track while it is present; otherwise the most confident tracked person.
        public static TrackedPerson SelectTarget(TrackedPerson[] persons, string currentTrackId)
        {
            TrackedPerson best = null;
            foreach (var p in persons)
            {
                if (p == null || string.IsNullOrWhiteSpace(p.track_id)) continue;
                if (p.tracking_state != "tracked" && p.tracking_state != "occluded") continue;
                if (currentTrackId != null && p.track_id == currentTrackId) return p;
                if (p.tracking_state == "tracked" && (best == null || p.confidence > best.confidence)) best = p;
            }
            return best;
        }

        public bool TryGetAnchorX(PoseLandmark[] landmarks, out float x)
        {
            x = 0.5f;
            if (landmarks == null || landmarks.Length != 33) return false;
            return TryAverageX(landmarks, 23, 24, out x) || TryAverageX(landmarks, 11, 12, out x);
        }

        private bool TryAverageX(PoseLandmark[] l, int a, int b, out float x)
        {
            x = 0f;
            int n = 0;
            foreach (int i in new[] { a, b })
            {
                if (l[i] != null && l[i].visibility >= anchorMinVisibility) { x += l[i].x; n++; }
            }
            if (n == 0) return false;
            x /= n;
            return true;
        }

        private bool IsHandRaised(PoseLandmark[] l)
        {
            if (l == null || l.Length != 33) return false;
            return WristAbove(l, 15, 11) || WristAbove(l, 16, 12);
        }

        private bool WristAbove(PoseLandmark[] l, int wrist, int shoulder)
        {
            return l[wrist] != null && l[shoulder] != null &&
                l[wrist].visibility >= actionMinVisibility && l[shoulder].visibility >= actionMinVisibility &&
                l[wrist].y <= l[shoulder].y - raisedHandMargin;
        }
    }
}
