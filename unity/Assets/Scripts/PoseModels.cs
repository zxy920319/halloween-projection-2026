using System;

[Serializable]
public sealed class PoseFrame
{
    public int version;
    public string type;
    public long frame_id;
    public long server_monotonic_ns;
    public string coordinate_space;
    public string units;
    public bool mirrored_input;
    public TrackedPerson[] persons;
}

[Serializable]
public sealed class TrackedPerson
{
    public string track_id;
    public string tracking_state;
    public float confidence;
    public PoseLandmark[] landmarks;
}

[Serializable]
public sealed class PoseLandmark
{
    public int id;
    public float x;
    public float y;
    public float z;
    public float visibility;
    public float presence;
}
