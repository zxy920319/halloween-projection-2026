using UnityEngine;

namespace Tracking
{
    /// <summary>
    /// Gives the imported skeleton its horror-realistic look at runtime: aged bone material,
    /// pitch-black sockets and glowing red eyes (emissive material plus small red point lights).
    /// Works with any shader exposing _BaseColor/_Color and optionally _EmissionColor.
    /// </summary>
    public sealed class SkeletonLookSetup : MonoBehaviour
    {
        private static readonly Color Bone = new Color(0.72f, 0.66f, 0.54f);
        private static readonly Color Shadow = new Color(0.20f, 0.17f, 0.14f);
        private static readonly Color Socket = new Color(0.01f, 0.005f, 0.005f);
        private static readonly Color EyeRed = new Color(1f, 0.02f, 0.01f);

        private void Start()
        {
            foreach (var renderer in GetComponentsInChildren<Renderer>(true))
            {
                if (renderer is ParticleSystemRenderer) continue;
                Material[] materials = renderer.materials;
                for (int i = 0; i < materials.Length; i++) Style(materials[i]);
                renderer.materials = materials;
            }
            AddEyeLights();
        }

        private static void Style(Material m)
        {
            if (m == null) return;
            string n = m.name.ToLowerInvariant();
            if (n.Contains("red_eye") || n.Contains("cursed"))
            {
                SetColor(m, EyeRed);
                if (m.HasProperty("_EmissionColor"))
                {
                    m.EnableKeyword("_EMISSION");
                    m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
                    m.SetColor("_EmissionColor", EyeRed * 6f);
                }
            }
            else if (n.Contains("socket")) SetColor(m, Socket);
            else if (n.Contains("shadow")) SetColor(m, Shadow);
            else if (n.Contains("ivory") || n.Contains("bone")) SetColor(m, Bone);
        }

        private static void SetColor(Material m, Color c)
        {
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            if (m.HasProperty("_Color")) m.SetColor("_Color", c);
        }

        private void AddEyeLights()
        {
            Transform head = null;
            foreach (var t in GetComponentsInChildren<Transform>(true))
                if (t.name == "Head") { head = t; break; }
            if (head == null || head.Find("EyeGlow_L") != null) return;

            // Camera looks along +Z, so the face points toward -Z; derive the head-local axes from that.
            float scale = Mathf.Max(0.01f, transform.lossyScale.y);
            Vector3 up = Vector3.up * scale, forward = Vector3.back * scale, right = Vector3.right * scale;
            Vector3 center = head.position + up * 0.17f + forward * 0.12f;
            foreach (float side in new[] { -1f, 1f })
            {
                var go = new GameObject(side < 0 ? "EyeGlow_L" : "EyeGlow_R");
                go.transform.SetParent(head, true);
                go.transform.position = center + right * (0.054f * side);
                var light = go.AddComponent<Light>();
                light.type = LightType.Point;
                light.color = EyeRed;
                light.intensity = 1.2f;
                light.range = 0.5f * scale;
                light.shadows = LightShadows.None;
            }
        }
    }
}
