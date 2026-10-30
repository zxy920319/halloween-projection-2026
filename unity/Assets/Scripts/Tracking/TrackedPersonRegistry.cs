using System.Collections.Generic;

namespace Tracking
{
    public sealed class TrackedPersonRegistry
    {
        private readonly Dictionary<string, int> slots = new Dictionary<string, int>();

        public IReadOnlyDictionary<string, int> Slots => slots;

        public int GetOrAssign(string trackId, int maxSlots)
        {
            if (string.IsNullOrWhiteSpace(trackId) || maxSlots <= 0)
            {
                return -1;
            }

            if (slots.TryGetValue(trackId, out int existing))
            {
                return existing;
            }

            var occupied = new HashSet<int>(slots.Values);
            for (int slot = 0; slot < maxSlots; slot++)
            {
                if (!occupied.Contains(slot))
                {
                    slots.Add(trackId, slot);
                    return slot;
                }
            }
            return -1;
        }

        public void RetainOnly(HashSet<string> activeTrackIds)
        {
            var expired = new List<string>();
            foreach (string trackId in slots.Keys)
            {
                if (!activeTrackIds.Contains(trackId))
                {
                    expired.Add(trackId);
                }
            }
            foreach (string trackId in expired)
            {
                slots.Remove(trackId);
            }
        }
    }
}
