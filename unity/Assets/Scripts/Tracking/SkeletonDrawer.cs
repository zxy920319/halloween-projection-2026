using UnityEngine;

namespace Tracking
{
    // Draws a simple bone skeleton from MediaPipe normalized-image landmarks.
    // Placeholder visual until a rigged Humanoid model is retargeted.
    public sealed class SkeletonDrawer : MonoBehaviour
    {
        private static readonly int[,] Bones =
        {
            {11, 12}, {11, 13}, {13, 15}, {12, 14}, {14, 16},
            {11, 23}, {12, 24}, {23, 24}, {23, 25}, {25, 27},
            {24, 26}, {26, 28}, {0, 11}, {0, 12}
        };

        [SerializeField] private Material lineMaterial;
        [SerializeField, Min(0.001f)] private float lineWidth = 0.03f;
        [SerializeField, Min(0.1f)] private float scale = 2f;
        [SerializeField, Range(0f, 1f)] private float minVisibility = 0.5f;
        [SerializeField] private bool mirror = true;

        private LineRenderer[] lines;

        private void Awake()
        {
            lines = new LineRenderer[Bones.GetLength(0)];
            for (int i = 0; i < lines.Length; i++)
            {
                var child = new GameObject($"bone_{i}");
                child.transform.SetParent(transform, false);
                var line = child.AddComponent<LineRenderer>();
                line.useWorldSpace = false;
                line.positionCount = 2;
                line.startWidth = lineWidth;
                line.endWidth = lineWidth;
                if (lineMaterial != null)
                {
                    line.sharedMaterial = lineMaterial;
                }
                line.enabled = false;
                lines[i] = line;
            }
        }

        public void Draw(PoseLandmark[] landmarks)
        {
            if (landmarks == null || landmarks.Length != 33)
            {
                return;
            }

            for (int i = 0; i < lines.Length; i++)
            {
                PoseLandmark a = landmarks[Bones[i, 0]];
                PoseLandmark b = landmarks[Bones[i, 1]];
                bool visible = a.visibility >= minVisibility && b.visibility >= minVisibility;
                lines[i].enabled = visible;
                if (visible)
                {
                    lines[i].SetPosition(0, ToLocal(a));
                    lines[i].SetPosition(1, ToLocal(b));
                }
            }
        }

        private Vector3 ToLocal(PoseLandmark p)
        {
            float x = (p.x - 0.5f) * scale * (mirror ? -1f : 1f);
            float y = (0.5f - p.y) * scale;
            return new Vector3(x, y, 0f);
        }
    }
}
