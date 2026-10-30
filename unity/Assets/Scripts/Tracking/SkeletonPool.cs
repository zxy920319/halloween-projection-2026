using System.Collections.Generic;
using System;
using UnityEngine;

namespace Tracking
{
    // Drop-in replacement for uploaded SkeletonPool.cs.
    // Prefers a real rig controller; retains SkeletonDrawer as debug fallback.
    public sealed class SkeletonPool : MonoBehaviour
    {
        [SerializeField] private GameObject[] skeletonRoots = new GameObject[3];
        [SerializeField, Min(0f)] private float horizontalSpacing = 1.5f;
        [SerializeField, Range(0f, 1f)] private float actionMinVisibility = 0.6f;
        [SerializeField, Range(0.01f, 1f)] private float raisedHandMargin = 0.12f;
        [SerializeField] private bool showIdleSkeletonWithoutTracking = true;
        private readonly TrackedPersonRegistry registry = new TrackedPersonRegistry();
        private readonly HashSet<string> raisedHandLastFrame = new HashSet<string>();

        public event Action<PoseActionEventArgs> PoseActionDetected;

        public GameObject GetSkeletonRoot(int slot)
        {
            return slot >= 0 && slot < skeletonRoots.Length ? skeletonRoots[slot] : null;
        }

        // Slot 0 is always visible (rest pose when nobody is tracked); other slots appear per tracked person.
        private void Awake()
        {
            for (int i = 0; i < skeletonRoots.Length; i++)
            {
                if (skeletonRoots[i] != null)
                {
                    skeletonRoots[i].SetActive(i == 0 && showIdleSkeletonWithoutTracking);
                }
            }
        }

        public void ApplyFrame(PoseFrame frame)
        {
            if (frame == null || frame.persons == null) return;
            int capacity = Mathf.Min(skeletonRoots.Length, 3);
            var active = new HashSet<string>();
            var driven = new HashSet<string>();
            foreach (var person in frame.persons)
            {
                if (person == null || string.IsNullOrWhiteSpace(person.track_id)) continue;
                // Occluded (uncertain identity) tracks keep their slot but are frozen, not re-driven.
                if (person.tracking_state == "tracked") { active.Add(person.track_id); driven.Add(person.track_id); }
                else if (person.tracking_state == "occluded") active.Add(person.track_id);
            }
            registry.RetainOnly(active);
            raisedHandLastFrame.RemoveWhere(trackId => !active.Contains(trackId));
            int count = Mathf.Min(active.Count, capacity);
            var liveSlots = new HashSet<int>();
            foreach (var person in frame.persons)
            {
                if (person == null || !active.Contains(person.track_id)) continue;
                int assigned = registry.GetOrAssign(person.track_id, capacity);
                if (assigned >= 0 && skeletonRoots[assigned] != null) liveSlots.Add(assigned);
            }
            // Spread live characters on one horizontal line, ordered by stable slot.
            var orderedSlots = new List<int>(liveSlots);
            orderedSlots.Sort();
            count = orderedSlots.Count;
            Vector3 lineOrigin = skeletonRoots.Length > 0 && skeletonRoots[0] != null
                ? skeletonRoots[0].transform.localPosition : Vector3.zero;
            liveSlots.Clear();
            var raisedHandThisFrame = new HashSet<string>();
            foreach (var person in frame.persons)
            {
                if (person == null || !active.Contains(person.track_id)) continue;
                int slot = registry.GetOrAssign(person.track_id, capacity);
                if (slot < 0 || skeletonRoots[slot] == null) continue;
                GameObject root = skeletonRoots[slot];
<<<<<<< HEAD
                root.SetActive(true);
                var drawer = root.GetComponent<SkeletonDrawer>();
                if (drawer != null)
                {
                    drawer.Draw(person.landmarks);
                }
                Vector3 position = root.transform.localPosition;
                position.x = MultiPersonLayout.GetHorizontalOffset(slot, visibleCount, horizontalSpacing);
                root.transform.localPosition = position;
=======
                liveSlots.Add(slot);
                if (!root.activeSelf) root.SetActive(true);
                Vector3 p = root.transform.localPosition;
                p.x = MultiPersonLayout.GetHorizontalOffset(orderedSlots.IndexOf(slot), count, horizontalSpacing);
                p.y = lineOrigin.y;
                p.z = lineOrigin.z;
                root.transform.localPosition = p;
                if (!driven.Contains(person.track_id)) continue;
                var driver = root.GetComponent<SkeletonPoseDriver>();
                if (driver == null) driver = root.GetComponentInChildren<SkeletonPoseDriver>();
                if (driver != null) driver.ApplyPose(person.landmarks, frame.mirrored_input);
                else
                {
                    var drawer = root.GetComponent<SkeletonDrawer>();
                    if (drawer != null) drawer.Draw(person.landmarks);
                }
                if (IsHandRaised(person.landmarks))
                {
                    raisedHandThisFrame.Add(person.track_id);
                    if (!raisedHandLastFrame.Contains(person.track_id))
                    {
                        PoseActionDetected?.Invoke(
                            new PoseActionEventArgs(person.track_id, slot, PoseActionEvent.HandRaised));
                    }
                }
>>>>>>> origin/master
            }
            raisedHandLastFrame.Clear();
            foreach (string trackId in raisedHandThisFrame)
            {
                raisedHandLastFrame.Add(trackId);
            }
            for (int i = 0; i < skeletonRoots.Length; i++)
            {
                GameObject root = skeletonRoots[i];
                if (root == null || liveSlots.Contains(i)) continue;
                bool keepIdle = i == 0 && showIdleSkeletonWithoutTracking;
                if (keepIdle)
                {
                    var idleDriver = root.GetComponentInChildren<SkeletonPoseDriver>(true);
                    if (idleDriver != null) idleDriver.ClearPose();
                    Vector3 idlePosition = root.transform.localPosition;
                    idlePosition.x = 0f;
                    root.transform.localPosition = idlePosition;
                }
                else if (root.activeSelf) root.SetActive(false);
            }
        }

        private bool IsHandRaised(PoseLandmark[] landmarks)
        {
            if (landmarks == null || landmarks.Length != 33)
            {
                return false;
            }
            return WristAboveShoulder(landmarks, 15, 11) || WristAboveShoulder(landmarks, 16, 12);
        }

        private bool WristAboveShoulder(PoseLandmark[] landmarks, int wristIndex, int shoulderIndex)
        {
            PoseLandmark wrist = landmarks[wristIndex];
            PoseLandmark shoulder = landmarks[shoulderIndex];
            return wrist != null && shoulder != null &&
                wrist.visibility >= actionMinVisibility && shoulder.visibility >= actionMinVisibility &&
                wrist.y <= shoulder.y - raisedHandMargin;
        }
    }
}
