using UnityEngine;

namespace Projection
{
    [DisallowMultipleComponent]
    public sealed class ProjectionEffectsController : MonoBehaviour
    {
        [SerializeField] private Tracking.SkeletonPool skeletonPool;
        [SerializeField] private Color handRaisedColor = new Color(1f, 0.28f, 0.03f, 1f);
        [SerializeField, Min(1)] private int particlesPerEvent = 28;
        [SerializeField, Min(0.1f)] private float effectHeight = 1.8f;
        [SerializeField, Min(0f)] private float eventCooldownSeconds = 1.25f;

        private readonly ParticleSystem[] effects = new ParticleSystem[3];
        private readonly float[] nextEventTime = new float[3];
        private Material particleMaterial;

        private void Awake()
        {
            if (skeletonPool == null)
            {
                skeletonPool = FindObjectOfType<Tracking.SkeletonPool>();
            }
            if (skeletonPool == null)
            {
                Debug.LogWarning("Projection effects are disabled because no SkeletonPool is assigned.", this);
                enabled = false;
                return;
            }
            skeletonPool.PoseActionDetected += OnPoseActionDetected;
            CreateParticleMaterial();
            for (int slot = 0; slot < effects.Length; slot++)
            {
                CreateEffect(slot);
            }
        }

        private void OnDestroy()
        {
            if (skeletonPool != null)
            {
                skeletonPool.PoseActionDetected -= OnPoseActionDetected;
            }
            if (particleMaterial != null)
            {
                Destroy(particleMaterial);
            }
        }

        private void CreateParticleMaterial()
        {
            Shader shader = Shader.Find("Particles/Standard Unlit");
            if (shader == null)
            {
                shader = Shader.Find("Sprites/Default");
            }
            if (shader == null)
            {
                throw new MissingComponentException("No supported built-in shader was found for projection effects.");
            }
            particleMaterial = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            if (particleMaterial.HasProperty("_Color"))
            {
                particleMaterial.color = handRaisedColor;
            }
        }

        private void CreateEffect(int slot)
        {
            var effectObject = new GameObject("HandRaisedParticles_" + slot);
            effectObject.transform.SetParent(transform, false);
            var particles = effectObject.AddComponent<ParticleSystem>();
            particles.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = particles.main;
            main.playOnAwake = false;
            main.loop = false;
            main.duration = 0.9f;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.45f, 0.9f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.8f, 2.4f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.035f, 0.09f);
            main.startColor = handRaisedColor;
            main.maxParticles = particlesPerEvent * 2;
            var emission = particles.emission;
            emission.enabled = false;
            var shape = particles.shape;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 45f;
            shape.radius = 0.15f;
            shape.rotation = new Vector3(-90f, 0f, 0f);
            var renderer = effectObject.GetComponent<ParticleSystemRenderer>();
            renderer.sharedMaterial = particleMaterial;
            renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            effects[slot] = particles;
        }

        private void OnPoseActionDetected(Tracking.PoseActionEventArgs poseEvent)
        {
            if (poseEvent == null || poseEvent.Action != Tracking.PoseActionEvent.HandRaised ||
                poseEvent.Slot < 0 || poseEvent.Slot >= effects.Length ||
                Time.unscaledTime < nextEventTime[poseEvent.Slot])
            {
                return;
            }

            GameObject character = skeletonPool.GetSkeletonRoot(poseEvent.Slot);
            if (character == null || effects[poseEvent.Slot] == null)
            {
                return;
            }
            nextEventTime[poseEvent.Slot] = Time.unscaledTime + eventCooldownSeconds;
            effects[poseEvent.Slot].transform.position =
                character.transform.position + character.transform.up * effectHeight;
            effects[poseEvent.Slot].Clear(true);
            effects[poseEvent.Slot].Emit(particlesPerEvent);
            Debug.Log($"Projection effect: hand-raised for track {poseEvent.TrackId} in slot {poseEvent.Slot}.", this);
        }
    }
}
