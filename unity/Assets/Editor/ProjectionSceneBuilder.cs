using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class ProjectionSceneBuilder
{
    public const string ScenePath = "Assets/Scenes/ProjectionCalibration.unity";
    private const string CharacterPrefabPath = "Assets/Prefabs/SkeletonCharacter.prefab";

    [MenuItem("Halloween Projection/Build Calibration Scene")]
    public static void BuildCalibrationScene()
    {
        Scene scene = BuildScene();
        Directory.CreateDirectory("Assets/Scenes");
        if (!EditorSceneManager.SaveScene(scene, ScenePath))
        {
            throw new InvalidOperationException($"Could not save projection scene at {ScenePath}.");
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"Built projection calibration scene at {ScenePath}.");
    }

    public static Scene BuildScene()
    {
        GameObject characterPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(CharacterPrefabPath);
        if (characterPrefab == null)
        {
            throw new InvalidOperationException($"Character prefab is missing: {CharacterPrefabPath}.");
        }

        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var cameraObject = new GameObject("ProjectionCamera");
        Camera camera = cameraObject.AddComponent<Camera>();
        cameraObject.tag = "MainCamera";
        cameraObject.transform.position = new Vector3(0f, 0f, -8f);
        camera.orthographic = true;
        camera.orthographicSize = 2.4f;
        camera.aspect = 16f / 9f;
        camera.nearClipPlane = 0.1f;
        camera.farClipPlane = 50f;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = Color.black;

        var calibration = cameraObject.AddComponent<Tracking.ProjectionCalibrationGrid>();
        SetObjectReference(calibration, "targetCamera", camera);
        SetBool(calibration, "visible", false);

        var display = cameraObject.AddComponent<Projection.ProjectionDisplayController>();
        SetObjectReference(display, "projectionCamera", camera);
        SetObjectReference(display, "calibrationGrid", calibration);
        SetInt(display, "targetDisplay", 0);
        SetBool(display, "mirrorHorizontal", false);
        SetBool(display, "startFullscreen", false);
        SetBool(display, "startCalibrationPattern", false);

        var keyLight = new GameObject("ProjectionKeyLight");
        Light light = keyLight.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1f;
        keyLight.transform.rotation = Quaternion.Euler(30f, -25f, 0f);

        var poolObject = new GameObject("SkeletonPool");
        var pool = poolObject.AddComponent<Tracking.SkeletonPool>();
        var roots = new GameObject[3];
        for (int i = 0; i < roots.Length; i++)
        {
            roots[i] = PrefabUtility.InstantiatePrefab(characterPrefab) as GameObject;
            if (roots[i] == null)
            {
                throw new InvalidOperationException($"Could not instantiate SkeletonCharacter prefab {i}.");
            }
            roots[i].name = "SkeletonCharacter_" + i;
            roots[i].transform.position = new Vector3(0f, -0.85f, 0f);
            roots[i].SetActive(false);
            SceneManager.MoveGameObjectToScene(roots[i], scene);
        }
        SetGameObjectArray(pool, "skeletonRoots", roots);

        var receiverObject = new GameObject("PoseReceiver");
        var receiver = receiverObject.AddComponent<PoseReceiver>();
        SetObjectReference(receiver, "skeletonPool", pool);

        var clientObject = new GameObject("PoseWebSocketClient");
        var client = clientObject.AddComponent<PoseWebSocketClient>();
        SetObjectReference(client, "receiver", receiver);

        var effectsObject = new GameObject("ProjectionEffects");
        var effects = effectsObject.AddComponent<Projection.ProjectionEffectsController>();
        SetObjectReference(effects, "skeletonPool", pool);

        var monitorObject = new GameObject("ProjectionRuntimeMonitor");
        var monitor = monitorObject.AddComponent<Projection.ProjectionRuntimeMonitor>();
        SetObjectReference(monitor, "poseReceiver", receiver);
        SetObjectReference(monitor, "poseClient", client);

        return scene;
    }

    private static void SetObjectReference(UnityEngine.Object target, string field, UnityEngine.Object value)
    {
        var serialized = new SerializedObject(target);
        serialized.FindProperty(field).objectReferenceValue = value;
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }

    private static void SetBool(UnityEngine.Object target, string field, bool value)
    {
        var serialized = new SerializedObject(target);
        serialized.FindProperty(field).boolValue = value;
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }

    private static void SetInt(UnityEngine.Object target, string field, int value)
    {
        var serialized = new SerializedObject(target);
        serialized.FindProperty(field).intValue = value;
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }

    private static void SetGameObjectArray(UnityEngine.Object target, string field, GameObject[] values)
    {
        var serialized = new SerializedObject(target);
        SerializedProperty array = serialized.FindProperty(field);
        array.arraySize = values.Length;
        for (int i = 0; i < values.Length; i++)
        {
            array.GetArrayElementAtIndex(i).objectReferenceValue = values[i];
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }
}
