using UnityEngine;

namespace Tracking
{
    public static class MultiPersonLayout
    {
        public static float GetHorizontalOffset(int slot, int count, float spacing)
        {
            if (count <= 1 || slot < 0 || slot >= count)
            {
                return 0f;
            }
            return (slot - (count - 1) * 0.5f) * spacing;
        }
    }
}
