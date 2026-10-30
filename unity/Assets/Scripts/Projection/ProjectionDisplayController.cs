using UnityEngine;
using UnityEngine.Rendering;

namespace Projection
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Camera))]
    public sealed class ProjectionDisplayController : MonoBehaviour
    {
        [SerializeField] private Camera projectionCamera;
        [SerializeField] private Tracking.ProjectionCalibrationGrid calibrationGrid;
        [SerializeField] private int targetDisplay;
        [SerializeField] private bool mirrorHorizontal;
        [SerializeField] private bool startFullscreen;
        [SerializeField] private bool startCalibrationPattern;
        [SerializeField] private bool keyboardControls = true;

        private bool previousInvertCulling;
        private bool ownsInvertCulling;
        private bool srpCallbacksRegistered;

        public bool MirrorHorizontal
        {
            get => mirrorHorizontal;
            set => mirrorHorizontal = value;
        }

        public int TargetDisplay => targetDisplay;

        private void Reset()
        {
            projectionCamera = GetComponent<Camera>();
            targetDisplay = 0;
        }

        private void Awake()
        {
            if (projectionCamera == null)
            {
                projectionCamera = GetComponent<Camera>();
            }
            if (projectionCamera == null)
            {
                throw new MissingComponentException("ProjectionDisplayController requires a Camera.");
            }
            if (targetDisplay < 0 || targetDisplay >= Display.displays.Length)
            {
                Debug.LogWarning(
                    $"Projection display {targetDisplay} is unavailable; using display 0.", this);
                targetDisplay = 0;
            }

            projectionCamera.targetDisplay = targetDisplay;
            if (targetDisplay > 0)
            {
                Display.displays[targetDisplay].Activate();
            }
            projectionCamera.clearFlags = CameraClearFlags.SolidColor;
            projectionCamera.backgroundColor = Color.black;
            if (startFullscreen)
            {
                Screen.fullScreenMode = FullScreenMode.FullScreenWindow;
                Screen.fullScreen = true;
            }
            if (calibrationGrid != null)
            {
                calibrationGrid.SetVisible(startCalibrationPattern);
            }
            ApplyProjectionSettings();
        }

        private void OnEnable()
        {
            if (GraphicsSettings.currentRenderPipeline != null)
            {
                RenderPipelineManager.beginCameraRendering += BeginSrpCamera;
                RenderPipelineManager.endCameraRendering += EndSrpCamera;
                srpCallbacksRegistered = true;
            }
        }

        private void OnDisable()
        {
            if (srpCallbacksRegistered)
            {
                RenderPipelineManager.beginCameraRendering -= BeginSrpCamera;
                RenderPipelineManager.endCameraRendering -= EndSrpCamera;
                srpCallbacksRegistered = false;
            }
            RestoreCulling();
            if (projectionCamera != null)
            {
                projectionCamera.ResetProjectionMatrix();
            }
        }

        private void LateUpdate()
        {
            ApplyProjectionSettings();
            if (!keyboardControls)
            {
                return;
            }

            if (Input.GetKeyDown(KeyCode.M))
            {
                mirrorHorizontal = !mirrorHorizontal;
                Debug.Log($"Projection optical mirror: {(mirrorHorizontal ? "ON" : "OFF")}.", this);
            }
            if (Input.GetKeyDown(KeyCode.C) && calibrationGrid != null)
            {
                calibrationGrid.SetVisible(!calibrationGrid.IsVisible);
                Debug.Log($"Projection calibration pattern: {(calibrationGrid.IsVisible ? "ON" : "OFF")}.", this);
            }
            if (Input.GetKeyDown(KeyCode.F))
            {
                Screen.fullScreen = !Screen.fullScreen;
            }
        }

        public void ApplyProjectionSettings()
        {
            if (projectionCamera == null)
            {
                return;
            }

            projectionCamera.ResetProjectionMatrix();
            if (mirrorHorizontal)
            {
                projectionCamera.projectionMatrix =
                    projectionCamera.projectionMatrix * Matrix4x4.Scale(new Vector3(-1f, 1f, 1f));
            }
        }

        private void OnPreCull()
        {
            if (!srpCallbacksRegistered)
            {
                PrepareCulling();
            }
        }

        private void OnPostRender()
        {
            if (!srpCallbacksRegistered)
            {
                RestoreCulling();
            }
        }

        private void BeginSrpCamera(ScriptableRenderContext context, Camera camera)
        {
            if (camera == projectionCamera)
            {
                PrepareCulling();
            }
        }

        private void EndSrpCamera(ScriptableRenderContext context, Camera camera)
        {
            if (camera == projectionCamera)
            {
                RestoreCulling();
            }
        }

        private void PrepareCulling()
        {
            if (!mirrorHorizontal || ownsInvertCulling)
            {
                return;
            }
            previousInvertCulling = GL.invertCulling;
            GL.invertCulling = !previousInvertCulling;
            ownsInvertCulling = true;
        }

        private void RestoreCulling()
        {
            if (!ownsInvertCulling)
            {
                return;
            }
            GL.invertCulling = previousInvertCulling;
            ownsInvertCulling = false;
        }
    }
}
