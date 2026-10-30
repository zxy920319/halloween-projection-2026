using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;

public static class SkeletonPoolValidation
{
    private const string ModelPath = "Assets/Models/HalloweenSkeleton.fbx";
    private const string PrefabPath = "Assets/Prefabs/SkeletonCharacter.prefab";
    private const string ResultPath = "Library/SkeletonPoolValidation-result.txt";

    public static void Run()
    {
        string resultPath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ResultPath));
        Directory.CreateDirectory(Path.GetDirectoryName(resultPath));
        try
        {
            ValidateImportedRig();
            GameObject prefab = CreateCharacterPrefab();
            ValidatePersonCounts(prefab);
            File.WriteAllText(resultPath, "PASS: Unity FBX import, rig/skin/material, prefab, and 1/2/3-person pose pool.");
            Debug.Log("SKELETON_POOL_VALIDATION_PASS");
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            File.WriteAllText(resultPath, exception.ToString());
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    private static void ValidateImportedRig()
    {
        var importer = AssetImporter.GetAtPath(ModelPath) as ModelImporter;
        if (importer == null)
        {
            throw new InvalidOperationException($"Could not import FBX at {ModelPath}.");
        }
        if (importer.animationType != ModelImporterAnimationType.Generic)
        {
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.SaveAndReimport();
        }

        GameObject model = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        if (model == null)
        {
            throw new InvalidOperationException("Unity did not load the Halloween skeleton FBX.");
        }

        var transforms = model.GetComponentsInChildren<Transform>(true);
        var names = new HashSet<string>(transforms.Select(transform => transform.name), StringComparer.Ordinal);
        string[] requiredBones =
        {
            "Hips", "Spine", "Chest", "Neck", "Head", "Jaw",
            "LeftShoulder", "RightShoulder", "LeftUpperArm", "LeftLowerArm", "LeftHand",
            "RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg",
            "LeftThumb", "LeftIndex", "LeftMiddle", "LeftRing", "LeftFoot", "LeftToes",
            "RightUpperLeg", "RightLowerLeg", "RightThumb", "RightIndex", "RightMiddle",
            "RightRing", "RightFoot", "RightToes"
        };
        var missingBones = requiredBones.Where(name => !names.Contains(name)).ToArray();
        if (missingBones.Length > 0)
        {
            throw new InvalidOperationException("FBX is missing rig bones: " + string.Join(", ", missingBones));
        }

        SkinnedMeshRenderer[] renderers = model.GetComponentsInChildren<SkinnedMeshRenderer>(true);
        if (renderers.Length == 0 || !renderers.Any(HasCompleteRigidWeights))
        {
            throw new InvalidOperationException(
                "FBX has no skinned mesh whose vertices each have one imported 1.0 bone weight.");
        }

        Material[] materials = AssetDatabase.LoadAllAssetsAtPath(ModelPath).OfType<Material>().ToArray();
        Material redEyeMaterial = materials.FirstOrDefault(material =>
            material.name.IndexOf("Cursed_Red_Eyes", StringComparison.OrdinalIgnoreCase) >= 0);
        if (redEyeMaterial == null)
        {
            throw new InvalidOperationException("FBX does not contain the expected Cursed_Red_Eyes material.");
        }
        if (!renderers.Any(renderer => renderer.sharedMaterials.Contains(redEyeMaterial)))
        {
            throw new InvalidOperationException("The red eye material is not assigned to the skinned mesh.");
        }
        Color eyeColor = redEyeMaterial.HasProperty("_BaseColor")
            ? redEyeMaterial.GetColor("_BaseColor")
            : redEyeMaterial.HasProperty("_Color") ? redEyeMaterial.GetColor("_Color") : Color.clear;
        if (eyeColor.r <= eyeColor.g * 2f || eyeColor.r <= eyeColor.b * 2f)
        {
            throw new InvalidOperationException($"Eye material is not red: {eyeColor}.");
        }

        Debug.Log($"FBX validation: {transforms.Length} transforms, {renderers.Length} skinned renderers, " +
                  $"{materials.Length} materials; required bones and red eye material found.");
    }

    private static bool HasCompleteRigidWeights(SkinnedMeshRenderer renderer)
    {
        if (renderer.sharedMesh == null || renderer.bones == null || renderer.bones.Length == 0)
        {
            return false;
        }

        BoneWeight[] weights = renderer.sharedMesh.boneWeights;
        if (weights.Length != renderer.sharedMesh.vertexCount)
        {
            return false;
        }
        foreach (BoneWeight weight in weights)
        {
            int weightedBones = 0;
            float total = 0f;
            for (int i = 0; i < 4; i++)
            {
                float value = i == 0 ? weight.weight0 : i == 1 ? weight.weight1 :
                    i == 2 ? weight.weight2 : weight.weight3;
                int boneIndex = i == 0 ? weight.boneIndex0 : i == 1 ? weight.boneIndex1 :
                    i == 2 ? weight.boneIndex2 : weight.boneIndex3;
                if (value > 0.0001f)
                {
                    if (boneIndex < 0 || boneIndex >= renderer.bones.Length || renderer.bones[boneIndex] == null)
                    {
                        return false;
                    }
                    weightedBones++;
                    total += value;
                }
            }
            if (weightedBones != 1 || Mathf.Abs(total - 1f) > 0.0001f)
            {
                return false;
            }
        }
        return true;
    }

    private static GameObject CreateCharacterPrefab()
    {
        GameObject model = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        var character = new GameObject("SkeletonCharacter");
        GameObject modelInstance = PrefabUtility.InstantiatePrefab(model) as GameObject;
        if (modelInstance == null)
        {
            UnityEngine.Object.DestroyImmediate(character);
            throw new InvalidOperationException("Could not instantiate imported FBX model.");
        }
        modelInstance.transform.SetParent(character.transform, false);

        var driver = character.AddComponent<Tracking.SkeletonPoseDriver>();
        var serializedDriver = new SerializedObject(driver);
        serializedDriver.FindProperty("rigRoot").objectReferenceValue = modelInstance.transform;
        serializedDriver.ApplyModifiedPropertiesWithoutUndo();

        Directory.CreateDirectory("Assets/Prefabs");
        GameObject prefab = PrefabUtility.SaveAsPrefabAsset(character, PrefabPath);
        UnityEngine.Object.DestroyImmediate(character);
        if (prefab == null)
        {
            throw new InvalidOperationException($"Could not save character prefab at {PrefabPath}.");
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"Created prefab {PrefabPath}.");
        return prefab;
    }

    private static void ValidatePersonCounts(GameObject prefab)
    {
        var poolObject = new GameObject("SkeletonPool");
        var roots = new GameObject[3];
        for (int i = 0; i < roots.Length; i++)
        {
            roots[i] = PrefabUtility.InstantiatePrefab(prefab) as GameObject;
            if (roots[i] == null)
            {
                throw new InvalidOperationException($"Could not instantiate character {i}.");
            }
            roots[i].name = "SkeletonCharacter_" + i;
            var driver = roots[i].GetComponent<Tracking.SkeletonPoseDriver>();
            var serializedDriver = new SerializedObject(driver);
            serializedDriver.FindProperty("mirrorInput").boolValue = false;
            serializedDriver.FindProperty("rotationSpeed").floatValue = 1000f;
            serializedDriver.ApplyModifiedPropertiesWithoutUndo();
            InvokeAwake(driver);
        }

        var pool = poolObject.AddComponent<Tracking.SkeletonPool>();
        var serializedPool = new SerializedObject(pool);
        serializedPool.FindProperty("skeletonRoots").arraySize = roots.Length;
        for (int i = 0; i < roots.Length; i++)
        {
            serializedPool.FindProperty("skeletonRoots").GetArrayElementAtIndex(i).objectReferenceValue = roots[i];
        }
        serializedPool.ApplyModifiedPropertiesWithoutUndo();

        pool.ApplyFrame(Frame(Person("one", 0f)));
        AssertActive(roots, 1);
        AssertPosition(roots[0], 0f);
        Transform drivenBone = FindDescendant(roots[0].transform, "LeftUpperArm");
        Quaternion restRotation = drivenBone.localRotation;
        Tracking.SkeletonPoseDriver firstDriver = roots[0].GetComponent<Tracking.SkeletonPoseDriver>();
        for (int i = 0; i < 10; i++)
        {
            InvokePoseUpdate(firstDriver, 0.1f);
        }
        if (Quaternion.Angle(restRotation, drivenBone.localRotation) < 0.1f)
        {
            object driven = typeof(Tracking.SkeletonPoseDriver).GetField(
                "driven", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(firstDriver);
            object newest = typeof(Tracking.SkeletonPoseDriver).GetField(
                "newest", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(firstDriver);
            throw new InvalidOperationException(
                $"A single person's pose did not rotate the imported left arm. Bound bones: " +
                $"{((System.Collections.ICollection)driven).Count}; cached landmarks: {newest != null}; " +
                $"rotation delta: {Quaternion.Angle(restRotation, drivenBone.localRotation)} degrees.");
        }

        pool.ApplyFrame(Frame(Person("one", 0f), Person("two", 0.25f)));
        AssertActive(roots, 2);
        AssertPosition(roots[0], -0.75f);
        AssertPosition(roots[1], 0.75f);
        InvokePoseUpdate(roots[0].GetComponent<Tracking.SkeletonPoseDriver>(), 0.1f);
        InvokePoseUpdate(roots[1].GetComponent<Tracking.SkeletonPoseDriver>(), 0.1f);
        Quaternion firstRotation = FindDescendant(roots[0].transform, "LeftUpperArm").localRotation;
        Quaternion secondRotation = FindDescendant(roots[1].transform, "LeftUpperArm").localRotation;
        if (Quaternion.Angle(firstRotation, secondRotation) < 1f)
        {
            throw new InvalidOperationException("Two people's distinct landmarks did not produce independent arm rotations.");
        }

        pool.ApplyFrame(Frame(Person("one", 0f), Person("two", 0.25f), Person("three", -0.25f)));
        AssertActive(roots, 3);
        AssertPosition(roots[0], -1.5f);
        AssertPosition(roots[1], 0f);
        AssertPosition(roots[2], 1.5f);
        for (int i = 0; i < roots.Length; i++)
        {
            InvokePoseUpdate(roots[i].GetComponent<Tracking.SkeletonPoseDriver>(), 0.1f);
        }
        Quaternion[] threePersonRotations = roots
            .Select(root => FindDescendant(root.transform, "LeftUpperArm").localRotation)
            .ToArray();
        for (int i = 0; i < threePersonRotations.Length; i++)
        {
            for (int j = i + 1; j < threePersonRotations.Length; j++)
            {
                if (Quaternion.Angle(threePersonRotations[i], threePersonRotations[j]) < 1f)
                {
                    throw new InvalidOperationException("Three distinct tracks did not produce independent arm rotations.");
                }
            }
        }

        pool.ApplyFrame(Frame(Person("one", 0f)));
        AssertActive(roots, 1);

        UnityEngine.Object.DestroyImmediate(poolObject);
        foreach (GameObject root in roots)
        {
            UnityEngine.Object.DestroyImmediate(root);
        }
    }

    private static TrackedPerson Person(string id, float elbowOffset)
    {
        var landmarks = new PoseLandmark[33];
        for (int i = 0; i < landmarks.Length; i++)
        {
            landmarks[i] = new PoseLandmark
            {
                id = i,
                x = 0.4f,
                y = 0.4f,
                visibility = 1f,
                presence = 1f
            };
        }
        landmarks[11].x = 0.4f;
        landmarks[11].y = 0.4f;
        landmarks[13].x = 0.4f + elbowOffset;
        landmarks[13].y = 0.7f;
        landmarks[15].x = 0.4f + elbowOffset;
        landmarks[15].y = 0.9f;
        return new TrackedPerson { track_id = id, tracking_state = "tracked", landmarks = landmarks };
    }

    private static PoseFrame Frame(params TrackedPerson[] people)
    {
        return new PoseFrame { version = 1, type = "pose", persons = people };
    }

    private static Transform FindDescendant(Transform root, string name)
    {
        foreach (Transform child in root.GetComponentsInChildren<Transform>(true))
        {
            if (child.name == name)
            {
                return child;
            }
        }
        throw new InvalidOperationException($"Could not find rig transform {name}.");
    }

    private static void InvokeAwake(Tracking.SkeletonPoseDriver driver)
    {
        MethodInfo method = typeof(Tracking.SkeletonPoseDriver).GetMethod("Awake",
            BindingFlags.Instance | BindingFlags.NonPublic);
        method.Invoke(driver, null);
    }

    private static void InvokePoseUpdate(Tracking.SkeletonPoseDriver driver, float deltaTime)
    {
        MethodInfo method = typeof(Tracking.SkeletonPoseDriver).GetMethod("UpdatePose",
            BindingFlags.Instance | BindingFlags.NonPublic);
        method.Invoke(driver, new object[] { deltaTime });
    }

    private static void AssertActive(GameObject[] roots, int expected)
    {
        int actual = roots.Count(root => root.activeSelf);
        if (actual != expected)
        {
            throw new InvalidOperationException($"Expected {expected} active characters, found {actual}.");
        }
    }

    private static void AssertPosition(GameObject root, float expectedX)
    {
        if (Mathf.Abs(root.transform.localPosition.x - expectedX) > 0.001f)
        {
            throw new InvalidOperationException(
                $"Expected {root.name} at x={expectedX}, got {root.transform.localPosition.x}.");
        }
    }
}
