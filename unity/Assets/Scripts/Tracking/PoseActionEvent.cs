namespace Tracking
{
    public enum PoseActionEvent
    {
        HandRaised
    }

    public sealed class PoseActionEventArgs
    {
        public PoseActionEventArgs(string trackId, int slot, PoseActionEvent action)
        {
            TrackId = trackId;
            Slot = slot;
            Action = action;
        }

        public string TrackId { get; }
        public int Slot { get; }
        public PoseActionEvent Action { get; }
    }
}
