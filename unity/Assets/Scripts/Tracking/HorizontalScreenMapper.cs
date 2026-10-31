using UnityEngine;

namespace Tracking
{
    public static class HorizontalScreenMapper
    {
        // Maps a normalized image x (0..1) to a world-space x in [-halfWidth, +halfWidth].
        // mirrored: flips the image so the skeleton acts like a mirror of the viewer.
        public static float Map(float normalizedX, bool mirrored, float halfWidth, float offset = 0f,
                                float scale = 1f, bool invert = false)
        {
            float x = Mathf.Clamp01(normalizedX);
            if (mirrored != invert) x = 1f - x;
            return Mathf.Lerp(-halfWidth, halfWidth, x) * scale + offset;
        }
    }
}
