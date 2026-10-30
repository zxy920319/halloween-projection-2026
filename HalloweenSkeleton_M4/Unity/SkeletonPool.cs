using System.Collections.Generic;
using UnityEngine;

namespace Tracking
{
    // Drop-in replacement for uploaded SkeletonPool.cs.
    // Prefers a real rig controller; retains SkeletonDrawer as debug fallback.
    public sealed class SkeletonPool : MonoBehaviour
    {
        [SerializeField] private GameObject[] skeletonRoots = new GameObject[3];
        [SerializeField, Min(0f)] private float horizontalSpacing = 1.5f;
        private readonly TrackedPersonRegistry registry = new TrackedPersonRegistry();

        public void ApplyFrame(PoseFrame frame)
        {
            if (frame == null || frame.persons == null) return;
            int capacity = Mathf.Min(skeletonRoots.Length, 3);
            var active = new HashSet<string>();
            foreach (var person in frame.persons)
            {
                if (person != null && !string.IsNullOrWhiteSpace(person.track_id)
                    && person.tracking_state == "tracked") active.Add(person.track_id);
            }
            registry.RetainOnly(active);
            int count = Mathf.Min(active.Count, capacity);
            var liveSlots = new HashSet<int>();
            foreach (var person in frame.persons)
            {
                if (person == null || !active.Contains(person.track_id)) continue;
                int slot = registry.GetOrAssign(person.track_id, capacity);
                if (slot < 0 || skeletonRoots[slot] == null) continue;
                GameObject root = skeletonRoots[slot];
                liveSlots.Add(slot);
                if (!root.activeSelf) root.SetActive(true);
                var driver = root.GetComponent<SkeletonPoseDriver>();
                if (driver == null) driver = root.GetComponentInChildren<SkeletonPoseDriver>();
                if (driver != null) driver.ApplyPose(person.landmarks, frame.mirrored_input);
                else
                {
                    var drawer = root.GetComponent<SkeletonDrawer>();
                    if (drawer != null) drawer.Draw(person.landmarks);
                }
                Vector3 p = root.transform.localPosition;
                p.x = MultiPersonLayout.GetHorizontalOffset(slot, count, horizontalSpacing);
                root.transform.localPosition = p;
            }
            for (int i = 0; i < skeletonRoots.Length; i++)
                if (skeletonRoots[i] != null && !liveSlots.Contains(i) && skeletonRoots[i].activeSelf)
                    skeletonRoots[i].SetActive(false);
        }
    }
}
