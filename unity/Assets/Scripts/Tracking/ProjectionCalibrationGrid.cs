using System.Collections.Generic;
using UnityEngine;

namespace Tracking
{
    [DisallowMultipleComponent]
    public sealed class ProjectionCalibrationGrid : MonoBehaviour
    {
        [SerializeField] private Camera targetCamera;
        [SerializeField, Min(2)] private int divisions = 10;
        [SerializeField, Min(0.001f)] private float lineWidth = 0.012f;
        [SerializeField] private Color gridColor = new Color(0.1f, 0.9f, 0.8f, 0.8f);
        [SerializeField] private bool visible;

        private readonly List<LineRenderer> lines = new List<LineRenderer>();
        private Material lineMaterial;
        private float cachedAspect;
        private float cachedOrthographicSize;

        public bool IsVisible => visible;
        public int LineCount => lines.Count;

        private void Awake()
        {
            if (targetCamera == null)
            {
                targetCamera = GetComponent<Camera>();
            }
            if (targetCamera == null)
            {
                throw new MissingComponentException("ProjectionCalibrationGrid requires a target Camera.");
            }
            Shader shader = Shader.Find("Sprites/Default");
            if (shader == null)
            {
                throw new MissingComponentException("Could not find the Sprites/Default shader for the calibration grid.");
            }
            lineMaterial = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            lineMaterial.color = gridColor;
            BuildLines();
            SetVisible(visible);
        }

        private void OnDestroy()
        {
            if (lineMaterial != null)
            {
                Destroy(lineMaterial);
            }
        }

        private void LateUpdate()
        {
            if (targetCamera != null &&
                (Mathf.Abs(targetCamera.aspect - cachedAspect) > 0.001f ||
                 Mathf.Abs(targetCamera.orthographicSize - cachedOrthographicSize) > 0.001f))
            {
                UpdateLines();
            }
        }

        public void SetVisible(bool show)
        {
            visible = show;
            foreach (LineRenderer line in lines)
            {
                if (line != null)
                {
                    line.enabled = show;
                }
            }
        }

        public void BuildLines()
        {
            if (targetCamera == null)
            {
                throw new MissingComponentException("Assign a target camera before building calibration lines.");
            }
            if (lineMaterial == null)
            {
                Shader shader = Shader.Find("Sprites/Default");
                if (shader == null)
                {
                    throw new MissingComponentException("Could not find the Sprites/Default shader.");
                }
                lineMaterial = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
                lineMaterial.color = gridColor;
            }

            for (int i = transform.childCount - 1; i >= 0; i--)
            {
                GameObject child = transform.GetChild(i).gameObject;
                if (Application.isPlaying)
                {
                    Destroy(child);
                }
                else
                {
                    DestroyImmediate(child);
                }
            }
            lines.Clear();
            for (int i = 0; i <= divisions; i++)
            {
                float fraction = i / (float)divisions;
                AddLine(
                    new Vector3(fraction, 0f, 0f),
                    new Vector3(fraction, 1f, 0f),
                    i == 0 || i == divisions || i == divisions / 2);
                AddLine(
                    new Vector3(0f, fraction, 0f),
                    new Vector3(1f, fraction, 0f),
                    i == 0 || i == divisions || i == divisions / 2);
            }
            UpdateLines();
            SetVisible(visible);
        }

        private void AddLine(Vector3 normalizedStart, Vector3 normalizedEnd, bool accent)
        {
            var lineObject = new GameObject("CalibrationLine_" + lines.Count);
            lineObject.transform.SetParent(transform, false);
            var line = lineObject.AddComponent<LineRenderer>();
            line.useWorldSpace = true;
            line.positionCount = 2;
            line.sharedMaterial = lineMaterial;
            line.startWidth = accent ? lineWidth * 1.8f : lineWidth;
            line.endWidth = line.startWidth;
            line.startColor = accent ? Color.white : gridColor;
            line.endColor = line.startColor;
            line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            line.receiveShadows = false;
            line.enabled = false;
            lines.Add(line);
            UpdateLine(line, normalizedStart, normalizedEnd);
        }

        private void UpdateLines()
        {
            float height = targetCamera.orthographic ? targetCamera.orthographicSize * 2f : 4f;
            float width = height * targetCamera.aspect;
            Vector3 center = targetCamera.transform.position +
                targetCamera.transform.forward * (targetCamera.nearClipPlane + 0.2f);
            int index = 0;
            for (int i = 0; i <= divisions; i++)
            {
                float fraction = i / (float)divisions;
                UpdateLine(lines[index++],
                    new Vector3(fraction, 0f, 0f), new Vector3(fraction, 1f, 0f), center, width, height);
                UpdateLine(lines[index++],
                    new Vector3(0f, fraction, 0f), new Vector3(1f, fraction, 0f), center, width, height);
            }
            cachedAspect = targetCamera.aspect;
            cachedOrthographicSize = targetCamera.orthographicSize;
        }

        private void UpdateLine(LineRenderer line, Vector3 start, Vector3 end)
        {
            if (targetCamera == null)
            {
                return;
            }
            float height = targetCamera.orthographic ? targetCamera.orthographicSize * 2f : 4f;
            UpdateLine(
                line, start, end,
                targetCamera.transform.position + targetCamera.transform.forward *
                    (targetCamera.nearClipPlane + 0.2f),
                height * targetCamera.aspect,
                height);
        }

        private void UpdateLine(
            LineRenderer line,
            Vector3 normalizedStart,
            Vector3 normalizedEnd,
            Vector3 center,
            float width,
            float height)
        {
            Vector3 origin = center - targetCamera.transform.right * (width * 0.5f) -
                targetCamera.transform.up * (height * 0.5f);
            line.SetPosition(0, origin + targetCamera.transform.right * (normalizedStart.x * width) +
                targetCamera.transform.up * (normalizedStart.y * height));
            line.SetPosition(1, origin + targetCamera.transform.right * (normalizedEnd.x * width) +
                targetCamera.transform.up * (normalizedEnd.y * height));
        }
    }
}
