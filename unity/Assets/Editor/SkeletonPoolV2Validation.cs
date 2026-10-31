using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class SkeletonPoolV2Validation
{
    private const string ResultPath = "Library/SkeletonPoolV2Validation-result.txt";

    public static void Run()
    {
        string resultPath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ResultPath));
        Directory.CreateDirectory(Path.GetDirectoryName(resultPath));
        try
        {
            ValidateMapper();
            ValidateTargetSelection();
            ValidatePool();
            File.WriteAllText(resultPath, "PASS: SkeletonPoolV2 mapping, selection, and visibility.");
            Debug.Log("SKELETON_POOL_V2_VALIDATION_PASS");
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            File.WriteAllText(resultPath, exception.ToString());
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    private static void ValidateMapper()
    {
        float left = Tracking.HorizontalScreenMapper.Map(0f, false, 4f);
        float mid = Tracking.HorizontalScreenMapper.Map(0.5f, false, 4f);
        float right = Tracking.HorizontalScreenMapper.Map(1f, false, 4f);
        Require(Mathf.Approximately(left, -4f) && Mathf.Approximately(mid, 0f) && Mathf.Approximately(right, 4f),
            "Mapper must be linear from -halfWidth to +halfWidth.");
        Require(Mathf.Approximately(Tracking.HorizontalScreenMapper.Map(0f, true, 4f), 4f),
            "Mirrored input must flip direction.");
        Require(Mathf.Approximately(Tracking.HorizontalScreenMapper.Map(0f, true, 4f, 0f, 1f, true), -4f),
            "invert must cancel mirrored.");
        Require(Mathf.Approximately(Tracking.HorizontalScreenMapper.Map(0.5f, false, 4f, 1f), 1f),
            "Offset must shift the result.");
    }

    private static void ValidateTargetSelection()
    {
        var a = Person("a", 0.6f, 0.3f, "tracked");
        var b = Person("b", 0.9f, 0.7f, "tracked");
        var people = new[] { a, b };
        Require(Tracking.SkeletonPoolV2.SelectTarget(people, null).track_id == "b",
            "Highest confidence person must be selected.");
        Require(Tracking.SkeletonPoolV2.SelectTarget(people, "a").track_id == "a",
            "Current track must be retained.");
        Require(Tracking.SkeletonPoolV2.SelectTarget(new[] { Person("c", 1f, 0.5f, "lost") }, null) == null,
            "Lost persons must not be selected.");
    }

    private static void ValidatePool()
    {
        var poolObject = new GameObject("SkeletonPoolV2");
        var root = new GameObject("Root");
        var pool = poolObject.AddComponent<Tracking.SkeletonPoolV2>();
        var serialized = new SerializedObject(pool);
        serialized.FindProperty("skeletonRoot").objectReferenceValue = root;
        serialized.ApplyModifiedPropertiesWithoutUndo();
        typeof(Tracking.SkeletonPoolV2).GetMethod("Awake",
            System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).Invoke(pool, null);
        Require(!root.activeSelf, "Skeleton must be hidden by default.");

        pool.ApplyFrame(new PoseFrame { persons = new TrackedPerson[0] });
        Require(!root.activeSelf, "Skeleton must stay hidden with no persons.");

        pool.ApplyFrame(new PoseFrame { persons = new[] { Person("a", 0.9f, 0.1f, "tracked") } });
        Require(root.activeSelf, "Skeleton must show when a person is tracked.");
        float leftX = root.transform.localPosition.x;
        pool.ApplyFrame(new PoseFrame { persons = new[] { Person("a", 0.9f, 0.9f, "tracked") } });
        InvokeUpdate(pool);
        for (int i = 0; i < 3; i++) InvokeUpdate(pool);
        Require(root.transform.localPosition.x >= leftX, "Moving right in the image must not move the skeleton left.");

        UnityEngine.Object.DestroyImmediate(poolObject);
        UnityEngine.Object.DestroyImmediate(root);
    }

    private static void InvokeUpdate(Tracking.SkeletonPoolV2 pool)
    {
        typeof(Tracking.SkeletonPoolV2).GetMethod("Update",
            System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).Invoke(pool, null);
    }

    private static TrackedPerson Person(string id, float confidence, float x, string state)
    {
        var landmarks = new PoseLandmark[33];
        for (int i = 0; i < landmarks.Length; i++)
            landmarks[i] = new PoseLandmark { id = i, x = x, y = 0.5f, visibility = 1f, presence = 1f };
        return new TrackedPerson { track_id = id, tracking_state = state, confidence = confidence, landmarks = landmarks };
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
