using UnityEngine;

public sealed class PoseReceiver : MonoBehaviour
{
    [SerializeField] private Tracking.SkeletonPool skeletonPool;

    public void ApplyJson(string json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            Debug.LogWarning("Ignoring empty pose message.", this);
            return;
        }

        PoseFrame frame;
        try
        {
            frame = JsonUtility.FromJson<PoseFrame>(json);
        }
        catch (System.ArgumentException exception)
        {
            Debug.LogWarning($"Ignoring invalid pose JSON: {exception.Message}", this);
            return;
        }

        if (frame == null || frame.version != 1 || frame.type != "pose" || frame.persons == null)
        {
            Debug.LogWarning("Ignoring pose message with unsupported shape/version.", this);
            return;
        }

        if (skeletonPool != null)
        {
            skeletonPool.ApplyFrame(frame);
        }
    }
}
