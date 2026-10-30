using System;
using System.Collections.Generic;
using UnityEngine;

namespace Tracking
{
    /// <summary>
    /// Drives the procedural HalloweenSkeleton rig using MediaPipe normalized-image
    /// landmarks. This is a first-pass 2.5D retargeter, NOT a calibrated 3D IK solver.
    /// It preserves the existing PoseFrame / SkeletonPool transport protocol.
    /// </summary>
    public sealed class SkeletonPoseDriver : MonoBehaviour
    {
        [SerializeField] private Transform rigRoot;
        [SerializeField, Range(0f, 1f)] private float minVisibility = 0.5f;
        [SerializeField] private bool mirrorInput = true;
        [SerializeField, Min(0.1f)] private float rotationSpeed = 16f;

        private struct Pair
        {
            public string Name;
            public int From, To;
            public Pair(string name, int from, int to) { Name = name; From = from; To = to; }
        }

        // MediaPipe 33-landmark indices. Order matters: parent before child.
        private static readonly Pair[] Mapping =
        {
            new Pair("Spine",  23, 11), // approximate torso; 11 is left shoulder
            new Pair("LeftUpperArm", 11, 13),
            new Pair("LeftLowerArm", 13, 15),
            new Pair("RightUpperArm", 12, 14),
            new Pair("RightLowerArm", 14, 16),
            new Pair("LeftUpperLeg", 23, 25),
            new Pair("LeftLowerLeg", 25, 27),
            new Pair("RightUpperLeg", 24, 26),
            new Pair("RightLowerLeg", 26, 28),
        };

        private sealed class DrivenBone
        {
            public Transform Bone;
            public Transform Tip;
            public Quaternion RestLocalRotation;
            public int From, To;
        }

        private readonly List<DrivenBone> driven = new List<DrivenBone>();
        private PoseLandmark[] newest;

        private void Awake()
        {
            if (rigRoot == null) rigRoot = transform;
            var transforms = rigRoot.GetComponentsInChildren<Transform>(true);
            var byName = new Dictionary<string, Transform>(StringComparer.Ordinal);
            foreach (var t in transforms) if (!byName.ContainsKey(t.name)) byName.Add(t.name, t);
            foreach (var entry in Mapping)
            {
                if (!byName.TryGetValue(entry.Name, out var b)) continue;
                Transform tip = null;
                if (b.childCount > 0) tip = b.GetChild(0);
                if (tip == null)
                {
                    Debug.LogWarning("Missing bone child for " + entry.Name, this);
                    continue;
                }
                driven.Add(new DrivenBone { Bone=b, Tip=tip, RestLocalRotation=b.localRotation,
                                             From=entry.From, To=entry.To });
            }
            Debug.Log($"SkeletonPoseDriver: bound {driven.Count}/{Mapping.Length} pose segments.", this);
        }

        public void ApplyPose(PoseLandmark[] landmarks, bool mirroredInput = false)
        {
            if (landmarks == null || landmarks.Length != 33) return;
            // Clone because upstream may reuse data arrays.
            newest = (PoseLandmark[])landmarks.Clone();
        }

        private void LateUpdate()
        {
            if (newest == null || rigRoot == null) return;
            // Keep limb bends from accumulating frame after frame. Do NOT reset in
            // an Animator-controlled rig unless you deliberately disable Animator.
            foreach (var item in driven) item.Bone.localRotation = item.RestLocalRotation;

            foreach (var item in driven)
            {
                PoseLandmark a = newest[item.From], b = newest[item.To];
                if (a == null || b == null || a.visibility < minVisibility || b.visibility < minVisibility)
                    continue;
                float sx = mirrorInput ? -1f : 1f;
                Vector3 desired = new Vector3(sx * (b.x - a.x), -(b.y - a.y), 0f);
                if (desired.sqrMagnitude < 0.000001f) continue;
                // Convert the 2D desired direction into the rig's XY (Unity world) plane.
                // Head-on mirror interaction uses screen X and world Y; world Z stays fixed.
                Vector3 targetWorld = transform.TransformDirection(desired.normalized);
                Vector3 restWorld = item.Tip.position - item.Bone.position;
                if (restWorld.sqrMagnitude < 0.000001f) continue;
                Quaternion correction = Quaternion.FromToRotation(restWorld, targetWorld);
                Quaternion targetRotation = correction * item.Bone.rotation;
                item.Bone.rotation = Quaternion.Slerp(item.Bone.rotation, targetRotation,
                    1f - Mathf.Exp(-rotationSpeed * Time.deltaTime));
            }
        }
    }
}
