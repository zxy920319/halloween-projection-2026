using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class ProjectionM5Validation
{
    public static void Run()
    {
        string resultPath = Path.GetFullPath(Path.Combine(Application.dataPath, "..",
            "Library/ProjectionM5Validation-result.txt"));
        Directory.CreateDirectory(Path.GetDirectoryName(resultPath));
        try
        {
            Scene scene = ProjectionSceneBuilder.BuildScene();
            Directory.CreateDirectory("Assets/Scenes");
            if (!EditorSceneManager.SaveScene(scene, ProjectionSceneBuilder.ScenePath))
            {
                throw new InvalidOperationException("Could not save generated projection calibration scene.");
            }

            var cameraObject = GameObject.Find("ProjectionCamera");
            Camera camera = cameraObject.GetComponent<Camera>();
            var display = cameraObject.GetComponent<Projection.ProjectionDisplayController>();
            var grid = cameraObject.GetComponent<Tracking.ProjectionCalibrationGrid>();
            if (camera.clearFlags != CameraClearFlags.SolidColor || camera.backgroundColor != Color.black ||
                camera.targetDisplay != 0)
            {
                throw new InvalidOperationException("Projection camera is not configured for a black display-0 output.");
            }

            SetBool(display, "mirrorHorizontal", false);
            display.ApplyProjectionSettings();
            float normalProjectionX = camera.projectionMatrix.m00;
            SetBool(display, "mirrorHorizontal", true);
            display.ApplyProjectionSettings();
            if (Mathf.Sign(camera.projectionMatrix.m00) != -Mathf.Sign(normalProjectionX))
            {
                throw new InvalidOperationException("Optical mirror setting did not horizontally flip the camera projection.");
            }
            SetBool(display, "mirrorHorizontal", false);
            display.ApplyProjectionSettings();

            grid.BuildLines();
            if (grid.LineCount < 20)
            {
                throw new InvalidOperationException($"Calibration pattern has too few lines: {grid.LineCount}.");
            }
            grid.SetVisible(true);
            if (!grid.IsVisible || grid.GetComponentsInChildren<LineRenderer>(true).Any(line => !line.enabled))
            {
                throw new InvalidOperationException("Calibration grid did not become visible.");
            }
            grid.SetVisible(false);

            PoseReceiver receiver = GameObject.Find("PoseReceiver").GetComponent<PoseReceiver>();
            var emptyFrame = "{\"version\":1,\"type\":\"pose\",\"frame_id\":71," +
                "\"server_monotonic_ns\":123,\"coordinate_space\":\"normalized_image\"," +
                "\"mirrored_input\":false,\"persons\":[]}";
            receiver.ApplyJson(emptyFrame);
            if (receiver.AcceptedFrames != 1 || receiver.LastFrameId != 71)
            {
                throw new InvalidOperationException("Pose receiver did not expose heartbeat frame status.");
            }

            Tracking.SkeletonPool pool = GameObject.Find("SkeletonPool").GetComponent<Tracking.SkeletonPool>();
            int actionCount = 0;
            Tracking.PoseActionEventArgs lastAction = null;
            pool.PoseActionDetected += poseEvent =>
            {
                actionCount++;
                lastAction = poseEvent;
            };
            pool.ApplyFrame(Frame(Person(false)));
            pool.ApplyFrame(Frame(Person(true)));
            pool.ApplyFrame(Frame(Person(true)));
            if (actionCount != 1 || lastAction == null ||
                lastAction.Action != Tracking.PoseActionEvent.HandRaised || lastAction.Slot != 0)
            {
                throw new InvalidOperationException("Raised-hand event was not emitted exactly once on the rising edge.");
            }

            Projection.ProjectionEffectsController effects =
                GameObject.Find("ProjectionEffects").GetComponent<Projection.ProjectionEffectsController>();
            InvokeAwake(effects);
            pool.ApplyFrame(Frame(Person(false)));
            pool.ApplyFrame(Frame(Person(true)));
            ParticleSystem[] particles = effects.GetComponentsInChildren<ParticleSystem>(true);
            if (particles.Length != 3 || particles[0].particleCount == 0)
            {
                throw new InvalidOperationException("Raised-hand pose event did not emit its particle effect.");
            }

            Projection.ProjectionRuntimeMonitor monitor =
                GameObject.Find("ProjectionRuntimeMonitor").GetComponent<Projection.ProjectionRuntimeMonitor>();
            InvokeAwake(monitor);
            monitor.EmitHeartbeat();

            AssetDatabase.SaveAssets();
            File.WriteAllText(resultPath,
                "PASS: black display output, horizontal mirror, calibration grid, pose heartbeat status, " +
                "rising-edge hand event, particle effect, and generated scene.");
            Debug.Log("PROJECTION_M5_VALIDATION_PASS");
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            File.WriteAllText(resultPath, exception.ToString());
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    private static void SetBool(UnityEngine.Object target, string propertyName, bool value)
    {
        var serialized = new SerializedObject(target);
        serialized.FindProperty(propertyName).boolValue = value;
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }

    private static void InvokeAwake(UnityEngine.Object target)
    {
        MethodInfo method = target.GetType().GetMethod("Awake",
            BindingFlags.Instance | BindingFlags.NonPublic);
        method.Invoke(target, null);
    }

    private static PoseFrame Frame(params TrackedPerson[] people)
    {
        return new PoseFrame { version = 1, type = "pose", persons = people };
    }

    private static TrackedPerson Person(bool handRaised)
    {
        var landmarks = new PoseLandmark[33];
        for (int i = 0; i < landmarks.Length; i++)
        {
            landmarks[i] = new PoseLandmark
            {
                id = i,
                x = 0.5f,
                y = 0.65f,
                visibility = 1f,
                presence = 1f
            };
        }
        landmarks[11].y = 0.5f;
        landmarks[12].y = 0.5f;
        landmarks[15].y = handRaised ? 0.2f : 0.65f;
        return new TrackedPerson
        {
            track_id = "projection-test-track",
            tracking_state = "tracked",
            confidence = 1f,
            landmarks = landmarks
        };
    }
}
