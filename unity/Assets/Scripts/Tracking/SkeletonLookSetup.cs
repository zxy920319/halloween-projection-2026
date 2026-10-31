using UnityEngine;

namespace Tracking
{
    /// <summary>
    /// Preserves the skeleton's aged bone and deep socket look on imported Unity materials.
    /// Works with any shader exposing _BaseColor/_Color and optionally _EmissionColor.
    /// </summary>
    public sealed class SkeletonLookSetup : MonoBehaviour
    {
        private static readonly Color Bone = new Color(0.72f, 0.66f, 0.54f);
        private static readonly Color Shadow = new Color(0.20f, 0.17f, 0.14f);
        private static readonly Color Socket = new Color(0.01f, 0.005f, 0.005f);
        private void Start()
        {
            foreach (var renderer in GetComponentsInChildren<Renderer>(true))
            {
                if (renderer is ParticleSystemRenderer) continue;
                Material[] materials = renderer.materials;
                for (int i = 0; i < materials.Length; i++) Style(materials[i]);
                renderer.materials = materials;
            }
        }

        private static void Style(Material m)
        {
            if (m == null) return;
            string n = m.name.ToLowerInvariant();
            if (n.Contains("socket")) SetColor(m, Socket);
            else if (n.Contains("shadow") || n.Contains("cancellous")) SetColor(m, Shadow);
            else if (n.Contains("ivory") || n.Contains("bone")) SetColor(m, Bone);
        }

        private static void SetColor(Material m, Color c)
        {
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            if (m.HasProperty("_Color")) m.SetColor("_Color", c);
        }

    }
}
