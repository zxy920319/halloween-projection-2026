using System;
using System.Collections.Generic;
using UnityEngine;

namespace Tracking
{
    /// <summary>
    /// Drives the procedural HalloweenSkeleton rig using MediaPipe normalized-image
    /// landmarks. This is a 2.5D retargeter (not a calibrated 3D IK solver): limbs follow
    /// landmark directions (including depth), the body yaws when the person turns, and the
    /// whole figure lifts when the person jumps. The idle pose has the arms hanging naturally.
    /// </summary>
    public sealed class SkeletonPoseDriver : MonoBehaviour
    {
        [SerializeField] private Transform rigRoot;
        [SerializeField, Range(0f, 1f)] private float minVisibility = 0.5f;
        [SerializeField] private bool mirrorInput = true;
        [SerializeField, Min(0.1f)] private float rotationSpeed = 16f;
        [SerializeField, Range(0f, 1.5f)] private float depthWeight = 0.7f;
        [SerializeField] private bool enableTurn = true;
        [SerializeField] private bool enableJump = true;
        [SerializeField, Min(0.1f)] private float turnSpeed = 7f;
        [SerializeField, Min(0.1f)] private float jumpSpeed = 18f;
        [SerializeField, Range(0f, 0.3f)] private float jumpDeadZone = 0.08f;
        [SerializeField, Min(0f)] private float maxJumpHeight = 1.4f;

        private struct Segment
        {
            public string Name, TipName;
            public int[] From, To;
            public bool UseDepth;
            public Vector3? RestDirection; // x is multiplied by the bone's outward side.
            public Segment(string name, string tip, int[] from, int[] to, bool depth, Vector3? rest = null)
            {
                Name = name; TipName = tip; From = from; To = to; UseDepth = depth; RestDirection = rest;
            }
        }

        // MediaPipe 33-landmark indices. Order matters: parent before child.
        private static readonly Segment[] Mapping =
        {
            new Segment("Spine", "Chest", new[] { 23, 24 }, new[] { 11, 12 }, false),
            new Segment("Neck", "Head", new[] { 11, 12 }, new[] { 7, 8 }, false),
            new Segment("LeftUpperArm", "LeftLowerArm", new[] { 11 }, new[] { 13 }, true, new Vector3(0.10f, -1f, 0f)),
            new Segment("LeftLowerArm", "LeftHand", new[] { 13 }, new[] { 15 }, true, new Vector3(0.04f, -1f, -0.08f)),
            new Segment("RightUpperArm", "RightLowerArm", new[] { 12 }, new[] { 14 }, true, new Vector3(0.10f, -1f, 0f)),
            new Segment("RightLowerArm", "RightHand", new[] { 14 }, new[] { 16 }, true, new Vector3(0.04f, -1f, -0.08f)),
            new Segment("LeftUpperLeg", "LeftLowerLeg", new[] { 23 }, new[] { 25 }, true),
            new Segment("LeftLowerLeg", "LeftFoot", new[] { 25 }, new[] { 27 }, true),
            new Segment("RightUpperLeg", "RightLowerLeg", new[] { 24 }, new[] { 26 }, true),
            new Segment("RightLowerLeg", "RightFoot", new[] { 26 }, new[] { 28 }, true),
        };

        private sealed class DrivenBone
        {
            public Transform Bone;
            public Transform Tip;
            public Quaternion RestLocalRotation;
            public Segment Segment;
        }

        private sealed class GroundBaseline
        {
            private float value;
            private bool initialized;

            public void Reset() { initialized = false; }

            // Returns how far (in image units) the sample is above the tracked ground level.
            public float Update(float current, float deltaTime)
            {
                if (!initialized) { value = current; initialized = true; }
                float rate = current > value ? 3f : 0.4f;
                value = Mathf.Lerp(value, current, 1f - Mathf.Exp(-rate * deltaTime));
                return Mathf.Max(0f, value - current);
            }
        }

        private readonly List<DrivenBone> driven = new List<DrivenBone>();
        private readonly GroundBaseline ankleBaseline = new GroundBaseline();
        private readonly GroundBaseline hipBaseline = new GroundBaseline();
        private PoseLandmark[] newest;
        private bool newestMirroredInput;
        private Quaternion rigRestLocalRotation = Quaternion.identity;
        private Vector3 rigRestLocalPosition;
        private float currentYaw;
        private float currentLift;
        private float rigTorsoLength = 0.55f;

        private void Awake()
        {
            if (rigRoot == null) rigRoot = transform;
            rigRestLocalRotation = rigRoot.localRotation;
            rigRestLocalPosition = rigRoot.localPosition;
            driven.Clear();
            var byName = new Dictionary<string, Transform>(StringComparer.Ordinal);
            foreach (var t in rigRoot.GetComponentsInChildren<Transform>(true))
                if (!byName.ContainsKey(t.name)) byName.Add(t.name, t);
            foreach (var entry in Mapping)
            {
                if (!byName.TryGetValue(entry.Name, out var bone)) continue;
                Transform tip = null;
                if (!string.IsNullOrEmpty(entry.TipName)) byName.TryGetValue(entry.TipName, out tip);
                if (tip == null && bone.childCount > 0) tip = bone.GetChild(0);
                if (tip == null)
                {
                    Debug.LogWarning("Missing bone child for " + entry.Name, this);
                    continue;
                }
                if (entry.RestDirection.HasValue) ApplyNaturalRest(bone, tip, entry.RestDirection.Value);
                driven.Add(new DrivenBone { Bone = bone, Tip = tip, RestLocalRotation = bone.localRotation,
                                            Segment = entry });
            }
            if (byName.TryGetValue("Hips", out var hips) && byName.TryGetValue("Neck", out var neck))
                rigTorsoLength = Mathf.Max(0.1f, Vector3.Distance(hips.position, neck.position));
            Debug.Log($"SkeletonPoseDriver: bound {driven.Count}/{Mapping.Length} pose segments.", this);
            if (GetComponent<SkeletonLookSetup>() == null) gameObject.AddComponent<SkeletonLookSetup>();
        }

        // The imported rig is modelled in a T-pose; rotate the arms so the idle pose hangs naturally.
        private void ApplyNaturalRest(Transform bone, Transform tip, Vector3 direction)
        {
            Vector3 current = tip.position - bone.position;
            if (current.sqrMagnitude < 1e-8f) return;
            float outward = Vector3.Dot(current, transform.right) < 0f ? -1f : 1f;
            Vector3 target = transform.TransformDirection(
                new Vector3(direction.x * outward, direction.y, direction.z)).normalized;
            bone.rotation = Quaternion.FromToRotation(current, target) * bone.rotation;
        }

        public void ApplyPose(PoseLandmark[] landmarks, bool mirroredInput = false)
        {
            if (landmarks == null || landmarks.Length != 33) return;
            if (newest == null) ResetMotionState();
            newest = (PoseLandmark[])landmarks.Clone();
            newestMirroredInput = mirroredInput;
        }

        public void ClearPose()
        {
            newest = null;
        }

        private void ResetMotionState()
        {
            ankleBaseline.Reset();
            hipBaseline.Reset();
        }

        private void LateUpdate()
        {
            UpdatePose(Time.deltaTime);
        }

        private bool Visible(int index)
        {
            PoseLandmark p = newest[index];
            return p != null && p.visibility >= minVisibility;
        }

        private bool AllVisible(int[] indices)
        {
            foreach (int i in indices) if (!Visible(i)) return false;
            return true;
        }

        private static Vector3 Average(PoseLandmark[] l, int[] indices, float sx)
        {
            Vector3 sum = Vector3.zero;
            foreach (int i in indices) sum += new Vector3(sx * l[i].x, -l[i].y, l[i].z);
            return sum / indices.Length;
        }

        private void UpdatePose(float deltaTime)
        {
            if (rigRoot == null) return;
            float blend = 1f - Mathf.Exp(-rotationSpeed * deltaTime);
            if (newest == null)
            {
                foreach (var item in driven)
                    item.Bone.localRotation = Quaternion.Slerp(item.Bone.localRotation, item.RestLocalRotation, blend);
                ApplyGlobalMotion(0f, 0f, deltaTime);
                return;
            }
            bool flipX = mirrorInput != newestMirroredInput;
            float sx = flipX ? -1f : 1f;
            foreach (var item in driven)
            {
                Segment s = item.Segment;
                if (!AllVisible(s.From) || !AllVisible(s.To))
                {
                    item.Bone.localRotation = Quaternion.Slerp(item.Bone.localRotation,
                        item.RestLocalRotation, blend);
                    continue;
                }
                Vector3 a = Average(newest, s.From, sx), b = Average(newest, s.To, sx);
                Vector3 desired = b - a;
                desired.z = s.UseDepth ? desired.z * depthWeight : 0f;
                if (desired.sqrMagnitude < 0.000001f) continue;
                Vector3 targetWorld = transform.TransformDirection(desired.normalized);
                Vector3 currentDirection = item.Tip.position - item.Bone.position;
                if (currentDirection.sqrMagnitude < 0.000001f) continue;
                Quaternion correction = Quaternion.FromToRotation(currentDirection, targetWorld);
                Quaternion targetRotation = correction * item.Bone.rotation;
                item.Bone.rotation = Quaternion.Slerp(item.Bone.rotation, targetRotation, blend);
            }
            ApplyGlobalMotion(EstimateYaw(sx), enableJump ? EstimateLift(deltaTime) : 0f, deltaTime);
        }

        // Body turn: angle of the shoulder/hip line in the horizontal (x, depth) plane.
        private float EstimateYaw(float sx)
        {
            if (!enableTurn) return 0f;
            Vector3 axis = Vector3.zero;
            if (AllVisible(new[] { 11, 12 })) axis += ShoulderLine(11, 12, sx);
            if (AllVisible(new[] { 23, 24 })) axis += ShoulderLine(23, 24, sx);
            if (axis.magnitude < 0.04f) return currentYaw;
            Vector3 frontal = Vector3.right * -sx;
            float yaw = Vector3.SignedAngle(frontal, axis, Vector3.up);
            return Mathf.Abs(yaw) < 10f ? 0f : yaw;
        }

        private Vector3 ShoulderLine(int left, int right, float sx)
        {
            return new Vector3(sx * (newest[right].x - newest[left].x), 0f, newest[right].z - newest[left].z);
        }

        // Jump height in world units, from ankles (or hips as a fallback) rising above their baseline.
        private float EstimateLift(float deltaTime)
        {
            if (!AllVisible(new[] { 11, 12, 23, 24 })) return 0f;
            Vector2 shoulders = new Vector2(newest[11].x + newest[12].x, newest[11].y + newest[12].y) * 0.5f;
            Vector2 hips = new Vector2(newest[23].x + newest[24].x, newest[23].y + newest[24].y) * 0.5f;
            float torso = Vector2.Distance(shoulders, hips);
            if (torso < 0.05f) return 0f;
            float rise;
            if (Visible(27) && Visible(28))
                rise = ankleBaseline.Update((newest[27].y + newest[28].y) * 0.5f, deltaTime);
            else
                rise = hipBaseline.Update(hips.y, deltaTime);
            float normalized = rise / torso - jumpDeadZone;
            if (normalized <= 0f) return 0f;
            return Mathf.Min(maxJumpHeight, normalized * rigTorsoLength);
        }

        private void ApplyGlobalMotion(float yaw, float lift, float deltaTime)
        {
            currentYaw = Mathf.LerpAngle(currentYaw, yaw, 1f - Mathf.Exp(-turnSpeed * deltaTime));
            currentLift = Mathf.Lerp(currentLift, lift, 1f - Mathf.Exp(-jumpSpeed * deltaTime));
            if (rigRoot == transform) return;
            rigRoot.localRotation = Quaternion.AngleAxis(currentYaw, Vector3.up) * rigRestLocalRotation;
            rigRoot.localPosition = rigRestLocalPosition + Vector3.up * currentLift;
        }
    }
}
