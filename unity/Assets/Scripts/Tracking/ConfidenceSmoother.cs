using UnityEngine;

namespace Tracking
{
    public static class ConfidenceSmoother
    {
        public static Vector3 LerpWhenConfident(
            Vector3 current, Vector3 target, float confidence, float deltaTime, float speed)
        {
            if (float.IsNaN(confidence) || confidence < 0.2f ||
                float.IsNaN(target.x) || float.IsNaN(target.y) || float.IsNaN(target.z))
            {
                return current;
            }

            float blend = 1f - Mathf.Exp(-Mathf.Max(0f, speed) * Mathf.Max(0f, deltaTime));
            return Vector3.Lerp(current, target, blend);
        }
    }
}
