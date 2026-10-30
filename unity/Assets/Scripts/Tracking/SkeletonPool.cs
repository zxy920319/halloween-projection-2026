using System.Collections.Generic;
using UnityEngine;

namespace Tracking
{
    public sealed class SkeletonPool : MonoBehaviour
    {
        [SerializeField] private GameObject[] skeletonRoots = new GameObject[3];
        [SerializeField, Min(0f)] private float horizontalSpacing = 1.5f;

        private readonly TrackedPersonRegistry registry = new TrackedPersonRegistry();

        public void ApplyFrame(PoseFrame frame)
        {
            if (frame == null || frame.persons == null)
            {
                return;
            }

            int capacity = Mathf.Min(skeletonRoots.Length, 3);
            var activeIds = new HashSet<string>();
            int visibleCount = 0;
            foreach (TrackedPerson person in frame.persons)
            {
                if (person == null || string.IsNullOrWhiteSpace(person.track_id) ||
                    person.tracking_state != "tracked")
                {
                    continue;
                }
                activeIds.Add(person.track_id);
                visibleCount++;
            }

            registry.RetainOnly(activeIds);
            foreach (GameObject root in skeletonRoots)
            {
                if (root != null)
                {
                    root.SetActive(false);
                }
            }

            foreach (TrackedPerson person in frame.persons)
            {
                if (person == null || !activeIds.Contains(person.track_id))
                {
                    continue;
                }
                int slot = registry.GetOrAssign(person.track_id, capacity);
                if (slot < 0 || skeletonRoots[slot] == null)
                {
                    continue;
                }

                GameObject root = skeletonRoots[slot];
                root.SetActive(true);
                Vector3 position = root.transform.localPosition;
                position.x = MultiPersonLayout.GetHorizontalOffset(slot, visibleCount, horizontalSpacing);
                root.transform.localPosition = position;
            }
        }
    }
}
