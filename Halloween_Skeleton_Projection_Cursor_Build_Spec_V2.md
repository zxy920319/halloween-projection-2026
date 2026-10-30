# Halloween Skeleton Mirror V2 — Cursor / GitHub Copilot 可执行工程任务书

> **版本**：V2.0 · 2026-10-19 · 多人架构 + 窗口开放式部署 + Pi 5 必选

> **用途**：把本文件放到空 Git 仓库根目录，命名为 `PROJECT_SPEC.md`，交给 Cursor Agent 或 GitHub Copilot Agent 实施。  
> **原则**：树莓派 5 是必需的现场采集节点；RTX 4090 电脑是 AI + Unity 渲染节点。不要绕过树莓派改为摄像头直接连电脑。  
> **状态**：软件开发规格，**不宣称已经验证 Astra Pro Plus 在 Raspberry Pi 5 ARM64 上可正常采集**。

## 0. Agent 执行指令（必须遵守）

你是一名高级嵌入式 / 计算机视觉 / 实时 3D 工程师。请在当前仓库中**实际创建代码、配置、脚本、测试、文档**，不要只输出实施建议。

1. 先检查仓库与运行环境；没有硬件时实现 mock source，不能虚构驱动成功或实机 FPS。
2. 逐阶段完成下方 **M0 → M1 → M2 → M3 → M4 → M5**。每阶段运行可执行测试，保存验证日志或在文档说明未测试的原因。
3. 保持 Raspberry Pi 5 位于端到端实时主链路中。树莓派负责采集和编码，服务器负责推理/渲染。**禁止将第一版架构改为摄像头直连服务器。**
4. 每阶段明确：新增文件、启动方法、测试结果、尚未解决的风险、下一阶段。
5. 不能假设 Orbbec SDK v2 支持 Astra Pro Plus；不能假设旧 Orbbec SDK / OpenNI2 已支持 Pi 5 ARM64。首先实现探测和 adapter 接口。
6. 禁止自动执行修改摄像头固件、下载不可信二进制、修改系统 USB 驱动或需要 `sudo` 的命令；这类操作必须列出命令并等待人类审批。
7. 除非明确获得授权，不上传儿童照片、视频、深度图或人体数据至互联网；局域网传输，不长期保存图像。默认不录制。
8. 对所有代码提供依赖锁定或明确版本范围、日志、异常处理与单元测试。出现外部依赖限制时诚实报告阻塞，但继续完成 mock 链路。
9. 不要把示意数据、mock 数据和真实测量混淆；在输出中标注来源。
10. 没有 Unity 编辑器自动化能力时，仍然生成完整 Unity C# 脚本、README 和可由人类在编辑器完成的最少配置步骤。

---

## 1. 项目目标与硬件

### 1.1 必备硬件

- 摄像头：**Orbbec Astra Pro Plus（结构光）**，计划在打开的窗户开口内侧或窗边三脚架上朝外拍摄；**镜头、红外发射器和接收器的整个光路不得穿过玻璃或全息反射膜**，USB 连接 **Raspberry Pi 5**。
- 边缘设备：**Raspberry Pi 5**，建议 Raspberry Pi OS 64-bit，使用 Gigabit Ethernet（Wi-Fi 仅次选）。
- 计算机：Windows 11 或 Linux 桌面机，NVIDIA **RTX 4090**。
- 显示：投影仪与待核验的“全息反射膜”（半透半反 / 逆反射膜的光学方式尚未确认）。玻璃可用于投影，**摄像头采集光路与玻璃/膜分离**。
- 安装：用户已有三脚架；**暂不把 Astra Pro Plus 的安装螺纹规格当作已确认事实**，必须看真实底座孔位、说明书或实物试拧正确转接件；稳定固定并配防坠措施。
- 网络：树莓派与电脑在同一个可信局域网；需配置静态 IP 或 DHCP 保留地址。
- 连接假设：投影仪能够通过 HDMI/DP 连接 RTX 4090 电脑。**如果投影仪也离电脑很远，此设计需要另行确定投影信号传输硬件；树莓派采集链路不能自动解决投影 HDMI 距离问题。**

### 1.2 交互目标

**软件与协议自第一天按最多三人设计；交付循序渐进：MVP 单人 → 两人 → 最多三人。** 每位被稳定追踪的儿童对应独立骷髅及临时 `track_id`，主要动作包含举手、下蹲、侧倾、转身与抬腿（视可见度降级）。人数变动时自动切换角色排布；检测到遮挡或身份不确定时允许冻结/淡出，不得强行把甲的动作交换给乙。第一版不要求手指或面部表情；多人并行属于后续里程碑，不冒充 MVP 已实现。

### 1.3 非功能性目标（目标，不是既有实测）

- 相机目标：640×480 @ 30 FPS；按设备实际支持格式调整。
- AI 姿态更新目标：20–30 Hz；Unity 渲染目标：60 FPS。
- 摄像头到投影显示端到端目标：≤150 ms，优化目标 ≤100 ms。每段都应打点；显示延迟需要外部实测。
- 丢帧时优先处理最新帧，不形成积压；最大队列长度 1–2。
- 连续运行至少 30 分钟用于初期验收，最终现场运行测试至少 2 小时。
- 软件协议支持最多 3 人；运行模式初始设 1 人；无云端上传。
- 三人模式的可靠性取决于相机实际视场、窗口净开口、照明和遮挡，现场测试达标才启用。

## 2. 固定系统架构

```text
[Child] → [Orbbec Astra Pro Plus]
                 │ USB (near camera)
                 ▼
       [Raspberry Pi 5 / ARM64]
       CameraAdapter (Orbbec/OpenNI2/UVC/mock)
       ├─ RGB capture → JPEG encode (or selectable H.264 if supported)
       ├─ Depth capture (OPTIONAL in MVP; device/SDK feasibility gate)
       ├─ monotonic capture timestamp + frame_id
       └─ WebSocket frame stream + health/status
                 │ Wired LAN preferred
                 ▼
      [RTX 4090 Windows/Linux PC]
       ingest service (Python)
       ├─ latest-frame queue / drop-old
       ├─ MediaPipe Pose Landmarker (num_poses configurable: 1..3)
       ├─ temporal identity association / lost-track recovery
       ├─ joint smoothing / confidence gating
       ├─ action events / pose coordinate metadata
       └─ WebSocket pose publisher on localhost
                 │
                 ▼
           [Unity Renderer]
       skeleton pool (1..3) / retarget + IK
       mirror toggle / calibration / black background
       audio + Halloween effects
                 │ GPU video output
                 ▼
          [Projector / Reflective Film]
```

**AI 推理在 RTX 4090 电脑，不在树莓派上。** MediaPipe Python 初版可使用 CPU 推理，不要声称安装 CUDA 就自动使用 RTX 4090。若达不到性能目标，再评估 ONNX Runtime / TensorRT 并保留现有接口。

## 3. 先消除的硬件不确定性（M0 强制）

### 3.1 客观现状

- Orbbec 官方 SDK v2 兼容表中 **Astra Pro Plus 不受 SDK v2 支持**。
- Orbbec 官方旧版 SDK / OpenNI2 文档列出 Astra Pro Plus；**这不等于 Raspberry Pi 5 + 最新 ARM64 OS 的预编译库已可用**。
- Astra Pro Plus 的 RGB 是否被系统作为 UVC/V4L2 节点暴露，以及深度 USB 接口能否通过旧版 SDK 工作，**必须在实机探测**。
- OpenCV `VideoCapture(0)` 不能被视为万能驱动方案。

### 3.2 在 Pi 5 上进行只读探测

开发 `scripts/pi_probe.sh`，打印并记录：

```bash
uname -a
uname -m
cat /etc/os-release
lsusb
lsusb -t
ls -lah /dev/video* 2>/dev/null || true
command -v v4l2-ctl && v4l2-ctl --list-devices || true
command -v v4l2-ctl && for dev in /dev/video*; do [ -e "$dev" ] && v4l2-ctl -d "$dev" --list-formats-ext || true; done
python3 --version
```

注意 `v4l2-ctl` 可能未安装，应优雅提示需要 `v4l-utils`，**不可静默 sudo 安装**。同时以只读方式检测 `ldconfig -p`、SDK `.so` 文件的 CPU 架构（`file`），判断 arm64/aarch64 兼容性，不能拿 x86_64 动态库在 Pi 上加载。

### 3.3 M0 决策树（必须严格执行）

**路径 A — RGB/Depth 均可读：** Orbbec/OpenNI2 专用 adapter，MVP 先传 RGB，同时输出深度能力标志；后续加入同步深度。

**路径 B — 仅 RGB 可读：** UVC/V4L2 adapter。仍可完成 RGB → MediaPipe → Unity 的**单人全身动作跟随 MVP**。将 depth 标记为 unavailable，不能伪造真实深度。深度距离互动进入待办；服务器优先使用 MediaPipe world landmarks（估计值，非真实测距）。

**路径 C — RGB/Depth 均不可读：** 仍完成 mock / file-source 端到端集成与所有网络和 Unity 代码；输出精确的兼容性诊断报告、已尝试的安全步骤、需要用户提供的信息。不得绕过 Pi 5 或假装硬件验证已成功。硬件层如确实不能支持，请提出**需要用户审批**的更换采集硬件建议，而不是自行假设已替换。

**不允许自动执行**：刷固件、修改驱动、执行未知安装脚本、从随机论坛下载预编译 `libOpenNI2.so`。

## 4. 技术栈

- Pi 5：Python 3.11+；`opencv-python` **只有 wheel/系统库可用时**使用；`v4l2` / OpenNI C++ wrapper 作为选项；`aiohttp` 或 `websockets`；JPEG 编码优先用可用的 OpenCV/Pillow。
- Desktop：Python 3.11+、`mediapipe` Pose Landmarker Tasks API、`numpy`、`opencv-python`、`aiohttp`/`websockets`、`pydantic`（可选）。验证依赖与 Windows/Linux 当前 Python 版本兼容后锁版本。
- Unity：优先 Unity LTS 版本，由本机已安装版本决定，C#、Humanoid Avatar、Animation Rigging（可选）；网络客户端 WebSocket 库应选有明确 Unity 支持的实现。若依赖暂不可用，先用内置可编译的 TCP/UDP 或可审阅的 WebSocket 包并记录原因。
- 测试：pytest、Python mock camera、协议集成测试；Unity PlayMode/EditMode（具备 Unity 环境时）。
- 网络：MVP 使用 **WebSocket over LAN**，Pi → Desktop 传压缩 JPEG 二进制图像帧，Desktop → Unity 本机发 JSON pose；可扩展为 H.264，但第一版避免过早优化。

## 5. 项目仓库结构（按此创建）

```text
halloween-skeleton-mirror/
├── PROJECT_SPEC.md
├── README.md
├── .gitignore
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CAMERA_COMPATIBILITY.md
│   ├── PI_SETUP.md
│   ├── DESKTOP_SETUP.md
│   ├── UNITY_SETUP.md
│   ├── PROTOCOL.md
│   ├── CALIBRATION.md
│   ├── TEST_REPORT.md
│   └── TROUBLESHOOTING.md
├── shared/
│   ├── protocol.py
│   └── schemas/
│       ├── frame-metadata.schema.json
│       └── pose.schema.json
├── pi_agent/
│   ├── pyproject.toml
│   ├── config.example.yaml
│   ├── main.py
│   ├── camera/
│   │   ├── base.py
│   │   ├── mock.py
│   │   ├── v4l2_rgb.py
│   │   └── orbbec_openni.py  # safe explicit NotImplemented if SDK unavailable
│   ├── transport.py
│   ├── diagnostics.py
│   └── tests/
├── desktop/
│   ├── pyproject.toml
│   ├── config.example.yaml
│   ├── main.py
│   ├── ingest.py
│   ├── pose_estimator.py
│   ├── pose_filter.py
│   ├── pose_publisher.py
│   ├── health.py
│   └── tests/
├── unity/
│   ├── README.md
│   └── Assets/Scripts/
│       ├── PoseReceiver.cs
│       ├── PoseModels.cs
│       ├── SkeletonRetargeter.cs
│       ├── ConfidenceSmoother.cs
│       ├── CalibrationController.cs
│       ├── ProjectionController.cs
│       ├── TrackingStateController.cs
│       └── DebugPoseVisualizer.cs
├── scripts/
│   ├── pi_probe.sh
│   ├── run_pi_mock.sh
│   ├── run_desktop.sh
│   ├── check_network.py
│   └── smoke_test.py
└── tests/
    ├── test_frame_protocol.py
    ├── test_pose_protocol.py
    ├── test_reconnect.py
    └── test_end_to_end_mock.py
```

允许增加模块，但不要无故删掉各层。跨设备脚本需要注明平台。

## 6. 帧协议（Pi → Desktop）

为了避免传整帧 JSON/base64 的浪费，设计一个**二进制 WebSocket 消息**：

```
[4-byte big-endian unsigned header_length]
[UTF-8 JSON metadata header]
[JPEG payload bytes]
```

示例 `metadata`：

```json
{
  "version": 1,
  "type": "rgb_frame",
  "source": "pi5-astra-pro-plus",
  "frame_id": 12345,
  "capture_monotonic_ns": 987654321000,
  "width": 640,
  "height": 480,
  "encoding": "jpeg",
  "jpeg_quality": 75,
  "depth_available": false
}
```

**校验要求：** 限制最大 header 和 payload 大小、检查 JPEG 解码失败、丢弃重复/乱序旧 `frame_id`；需显式的协议版本和健康消息。`capture_monotonic_ns` 只可用于**同一台主机**内部计时，跨 Pi/PC 不能直接相减计算单程时延（时钟不同）。若要量测跨主机延迟，设计 NTP/时间同步误差报告或端到端可视化测试，不得给出伪精确值。

Pi network agent 连接 Desktop 的 `ws://<SERVER_LAN_IP>:8765/frames`，重连指数退避（例如 1s、2s、4s，最高 10s），心跳和连接状态日志。服务端只保留最新帧，避免积压。网络绑定到 LAN IP（示例），**禁止无鉴权直接对公网开放**。首次原型可在可信私有局域网使用无 TLS websocket，但必须文档提示风险；如网络不可信，启用 WSS / VPN 和设备鉴权。

## 7. 骨骼协议（Desktop → Unity）

每个有效推理结果一条 JSON；没有人的时候输出明确的 `tracking:false`，不要保持永久的“最后一帧有效”状态。

```json
{
  "version": 1,
  "type": "pose",
  "frame_id": 12345,
  "server_monotonic_ns": 1234567890123,
  "coordinate_space": "mediapipe_world",
  "units": "meters_estimated",
  "mirrored_input": false,
  "persons": [
    {
      "track_id": "session-1",
      "tracking_state": "tracked",
      "confidence": 0.95,
      "landmarks": [
        {"id": 0, "x": 0.01, "y": -0.45, "z": 0.12, "visibility": 0.98, "presence": 0.99}
      ],
      "events": {"left_hand_up": false, "right_hand_up": true, "squat": false}
    }
  ]
}
```

说明：每位 `persons[i].landmarks` 实际应包含 33 点；示例仅给一个点。`track_id` 为**现场临时跟踪 ID**，不能当作真实姓名或跨会话身份；MediaPipe 多姿态输出**不保证持久 ID**，必须独立实现关联器。`tracking_state` 建议枚举 `tracked | occluded | lost`。`persons=[]` 表示当前无人，过期轨迹单独通过生命周期管理，不能永远保留。不要把估计 `world_landmarks` 冒充 Orbbec 的真实 3D 深度坐标。`mirrored_input` 表示识别前是否镜像，Unity 投影翻转另行处理。服务端 pose publisher 默认 `ws://127.0.0.1:8766/poses`。

所有人体检测缺失时发送 `persons: []`；个别追踪丢失时在可配置的 0.3–1.0 秒内冻结、淡出或回待机动作。对于交叉遮挡造成的身份不确定，**宁可隐藏该骷髅，也不能静默交换控制权**。轨迹 ID 只在当前会话有效。

## 8. 坐标与 Unity Retargeting

**禁止直接把关节点世界位置赋给骨骼 Transform.position。** 必须实现：

1. MediaPipe 33 landmarks → 躯干与四肢的关键段方向；建立肩-髋定义的 body basis / local coordinate frame。
2. 处理 MediaPipe 与 Unity 的坐标系、轴定义、单位和手性差异，提供小型可测试变换矩阵或转换函数。
3. Unity 角色应预先 rig 为 Humanoid，记录 T-pose/bind-pose 和每个 Transform 的局部旋转偏移。
4. 先上半身 MVP：头、肩、上臂、前臂、躯干；再双腿、骨盆、膝盖和足底 IK。
5. 关节旋转计算可用 `Quaternion.FromToRotation` / `LookRotation` + bind offset，但必须处理 twist 歧义、关节极限、退化向量/零长度、姿态不可信。
6. 屏幕镜像与光学反射镜像是**两个独立开关**，不允许通过交换“左腕”“右腕”的语义标签来掩盖方向错误。
7. 加入 One Euro Filter 或适当的指数平滑；关节置信度低时保持/插值并限制抖动，丢失人后渐变到 Idle。
8. debug overlay 可显示 2D landmark、3D axis、关节名称、tracking state、FPS 和关键时延。

### 核心 MVP 验收动作

- 右手举起 → 对应骷髅手臂抬起；左手同理。
- 双手平举 → 骷髅双臂平举，无 180 度骨骼翻转。
- 头左右倾斜 → 骷髅头自然倾斜。
- 蹲下 → 骷髅髋/膝动作方向正确（足底 IK 可以延后完善）。
- 遮挡 0.5 秒 → 没有骨骼爆炸、NaN、瞬间旋转，追踪恢复后动作平滑。

## 9. 相机 adapter 接口

定义 `CameraSource` 抽象接口，返回 `CameraFrame`：

- `start()` / `read_latest()` / `stop()` / `capabilities()`。
- `CameraFrame` 包含 `frame_id`、`capture_monotonic_ns`、RGB numpy frame，以及 `optional_depth` 与深度单位（如果确实支持）。
- `MockCameraSource` 生成带帧编号与可视图案的合成 RGB 帧，用于脱离硬件的局域网集成测试。
- `V4L2CameraSource` 枚举 `/dev/video*`，根据设备报告选择正确节点与像素格式，而不是死写 index 0。
- `OrbbecOpenNI2CameraSource` 只在安装**确认与 ARM64 兼容**的官方 SDK 库之后实现；否则返回清晰的 unsupported 诊断，不捕获错误后偷偷切到其他摄像头。
- 深度流适配器须标注距离单位、坏点值、帧同步策略、RGB-depth registration 状态。

## 10. 深度融合（MVP 可后置，但接口必须存在）

- RGB 中的关键点 `(u_rgb,v_rgb)` 与深度图 `(u_depth,v_depth)` 不一定直接对应。
- 读取摄像机内参、RGB/Depth 之间外参或 SDK 官方 registration；无标定时不准声称获得可靠米制关节点。
- 深度有效时在像素邻域取有效深度中位数，投影到 camera-space 3D，并给置信度。
- 无深度时继续 RGB-only 模式，不允许合成假深度并当真值使用。
- 距离互动（靠近、后退）只有深度/校准来源可信才启用，否则 UI 显示 `distance_unavailable`。

## 11. 里程碑与必须交付内容

### M0 — 驱动与环境探测（必须第一步）

**交付：** `scripts/pi_probe.sh`、`docs/CAMERA_COMPATIBILITY.md`、设备能力日志模板、实际结果/待人工验证项目。

**验收：** 真实 Pi 上可一键运行只读探测。没有 Pi 访问时，明确未验证，不写“通过”。

### M1 — Pi mock JPEG 传输 → Desktop 预览

**交付：** 协议编码解码、Pi mock 数据流、Desktop WebSocket ingest、简单实时预览、断线重连、帧率计数、pytest。

**验收：** 在双机局域网或单机模拟中显示连续图像；手动断开连接后可自动重连；不会堆积旧帧。

### M2 — Pi 真摄像头 RGB 采集

**交付：** V4L2/UVC 适配器（若可用）与官方 OpenNI adapter 插口、设备发现、正确报错、配置文件、部署手册。

**验收：** 仅当真实摄像头读到带帧编号的新鲜帧时标记通过；如不兼容，写出可复现的 blocker，同时保留 M1 可运行。

### M3 — Desktop Pose Landmarker 与骨骼协议

**交付：** MediaPipe Tasks 实时推理、33 landmarks、pose JSON、置信度过滤、tracking=false 逻辑、2D debug viewer、单元测试。

**验收：** 使用 Pi RGB 或测试视频在桌面端完成骨骼追踪；如果只有 mock 图像不能识别人，需要提供单独的合规测试视频输入（本地文件、不提交仓库）。

### M4 — Unity 骷髅实时驱动

**交付：** Unity C# 网络接收、模型映射、上半身 retarget、基本四肢 IK/旋转、插值、丢失追踪恢复、骨骼 debug GUI、Unity setup 文档。

**验收：** 使用合成骨骼输入可驱动 rig，真人举手/倾斜时自然响应；所有实际通过情况需注明验证设备。

### M5 — 投影、万圣节特效、运行保障

**交付：** 黑背景渲染、光学镜像开关、投影校准场景、事件驱动特效、心跳/日志、自动重启配置示例（Pi systemd；Desktop 根据 OS 选任务计划或 systemd）、端到端时延测试说明。

**验收：** 单人互动稳定运行 30 分钟、画面方向正确、断线重连自动恢复。2 小时现场测试属于发布前验收。

## 12. 开发配置文件要求

`pi_agent/config.example.yaml` 至少含：

```yaml
camera:
  backend: mock  # mock | v4l2 | orbbec_openni2
  width: 640
  height: 480
  fps: 30
  device: auto
network:
  server_url: ws://192.168.1.100:8765/frames  # EDIT ME
  reconnect_max_seconds: 10
stream:
  jpeg_quality: 75
  max_pending_frames: 1
privacy:
  record_frames: false
```

`desktop/config.example.yaml` 至少含：

```yaml
ingest:
  host: 0.0.0.0   # bind only on trusted LAN; firewall restrict source to Pi IP
  port: 8765
pose:
  model_path: models/pose_landmarker_lite.task  # user-provided official download
  num_poses: 1  # 运行时阶段性增加至 2, 3；管线结构从开始支持多人
  max_persons: 3
  identity_tracking: true
  lost_track_timeout_ms: 1000
  min_detection_confidence: 0.5
  min_tracking_confidence: 0.5
publish:
  host: 127.0.0.1
  port: 8766
runtime:
  latest_frame_only: true
  show_debug_preview: true
projection:
  auto_layout: true
  max_skeletons: 3
  fallback_to_single_person: true
```

模型文件、私有影像、SDK 动态库不纳入 Git，提供官方地址与人工安装说明；版权和许可遵守原发布方要求。

## 13. 工程质量与测试

自动化测试至少包括：

- [ ] 二进制 frame 编码/解码回环与 malformed/oversized packet 拒绝。
- [ ] 乱序 `frame_id` 被丢弃。
- [ ] Pi 断线再连接与服务端恢复。
- [ ] 旧帧被丢弃，不增加队列延迟。
- [ ] `persons: []` 和每人 33 landmarks 校验。
- [ ] 人体关键点为空、部分不可信、NaN/Inf 时仍不会崩溃。
- [ ] 坐标系左右方向变换的已知输入测试。
- [ ] 骨骼分段方向零长度防护。
- [ ] 安全缺省：不录制、不公网开放、摄像头读取失败不会默默伪装成功。
- [ ] Pi mock → Desktop fake-pose 或模型服务 → Unity 的端到端可复现演示；明确 mock vs real。

记录 `capture_fps`, `received_fps`, `inference_fps`, `render_fps`, `frame_drop_count`, `reconnect_count`，以及各设备自己时钟上可精确计算的 processing duration。跨设备总延迟应通过 LED/高速手机视频或准确时钟同步实测。

## 14. 现场安装与儿童安全

- 相机固定，避免儿童碰撞或拉扯 USB；树莓派供电须符合官方要求。
- 优先使用有线网络；电缆走线并防绊倒。
- 骷髅特效/音量适合儿童，可一键关闭惊吓效果。
- 不在公共 Wi-Fi 上裸露视频服务；不默认录像，也不记录身份信息。
- 安装投影仪时避免强光直射眼睛，投影仪留足散热距离。
- 反射膜的具体类型、视角、镜像方向需现场校准；不假定所有“反光膜”都支持 45° Pepper's Ghost 布局。

## 15. 最新依赖/官方参考（实施时再次核对）

- Orbbec SDK v2 的设备支持说明（Astra Pro Plus 不受 v2 支持）：https://orbbec.github.io/OrbbecSDK_v2/
- Orbbec SDK v1 及设备表：https://orbbec.github.io/OrbbecSDK/
- Orbbec 官方 SDK 下载：https://www.orbbec.com/developers/orbbec-sdk/
- Orbbec OpenNI2：https://github.com/orbbec/OpenNI_SDK
- Google MediaPipe Pose Landmarker：https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python
- Unity 文档：https://docs.unity3d.com/

## 16. Agent 现在就开始的任务（无需再提笼统问题）

请**立即开始 M0 + M1**，不要等用户回答架构问题：

1. 扫描仓库并创建上述目录及必要的最小 `pyproject.toml`、README、示例配置。
2. 实现平台安全的 `pi_probe.sh`，生成诊断数据格式和 `CAMERA_COMPATIBILITY.md`。
3. 实现可运行的 `MockCameraSource`、带边界检查的 frame binary protocol、Pi WebSocket client、Desktop WebSocket server、实时预览。
4. 实现断线重连、最新帧队列、单元测试、smoke test、Pi/Windows/Linux 运行命令。
5. 如果仓库运行环境当前并不在树莓派上，不要伪造摄像头测试；必须明确列出用户需要在 Pi 上执行的唯一下一条探测命令。
6. 继续建立 Desktop MediaPipe 与 Unity 的接口骨架，但不可宣称 Unity 真机测试成功。
7. 最终输出：创建的文件树、已经运行的命令与结果、能直接复制的启动命令、M0/M1 完成程度、M2 的实际阻塞。

**用户硬性约束重复确认：树莓派 5 必须始终位于摄像头和 RTX 4090 之间的实时数据路径上，不能以“先插电脑测试”为由绕过树莓派。**


---

## 17. V2 场地约束与安装验收（强制新增）

### 17.1 固定部署方式

```text
窗外儿童互动区 (计划同时 1–3 人)
      │  无玻璃/膜遮挡的可见光 + 红外视线
      ▼
[打开的窗户开口]  ← Astra Pro Plus 镜头朝外，牢固安装在三脚架上
      │   短 USB 数据线，不夹线、不让窗扇碰撞设备
      ▼
[室内 Raspberry Pi 5] ← 有线 Ethernet 优先
      │  局域网帧流
      ▼
[室内 RTX 4090 PC] → Unity 多角色 → 投影仪 → 玻璃/反射膜
```

1. 首选 **摄像头在室内、朝向打开窗户的无障碍开口**；不是隔玻璃、隔膜拍摄。户外临时架设仅作为备选，必须解决雨、凝露和非户外设备温湿度限制。
2. 摄像头前方的结构光发射器、接收器、RGB 镜头均不能被窗框、纱窗、镜面膜、雨滴或玻璃遮挡；屋檐与窗扇不应遮挡纵向/横向视野。
3. 三脚架落在坚固且平整的室内地面，不在不稳定窗台上搭边；加防坠绳、配重和走线固定。不可把未核实的安装孔径/螺纹当作采购依据；先实拍底座并量测适配。
4. 确保窗扇不会被风吹动夹住镜头或 USB 线；窗户开口会改变室内保温与安全边界，成年人全程看护。
5. 保持镜头尽量正面朝向活动区，**初始**高度约 1.4–1.8 m、轻俯角约 0–15°，具体以 RGB 全身可见、深度图有效和透视遮挡少为准，不强制固定角度。建议室外 2–3 m 起试，量测真实可用距离。
6. 在实际夜间光照条件下验证 RGB 画面（包括投影开启时的串光），确保儿童脚部在画面内；适当增加室外柔和照明，避免照射眼睛和造成结构光过曝。
7. 如果深度不稳定，以 **RGB-only** 完成人体姿态识别；深度不是主流程的强依赖。Astra Pro Plus 不是防水户外设备，临时外放必须有天气与温度检查，不能以一层随意玻璃罩取代安全设计。

### 17.2 安装记录表（由 Agent 生成 `docs/SITE_SURVEY.md` 模板，现场填写）

- 窗口类型（上悬/平开/推拉）、净开口宽高、打开后的窗扇位置
- 摄像头实际距地高度、俯角、RGB/Depth 有效视场、距儿童站位距离
- 投影膜具体型号与光学种类（半透半反 / 逆反射 / 其他）、窗内外位置
- 相机到树莓派 USB 线长、树莓派到 PC 网络拓扑、投影视频线长
- 摄像头底座三脚架孔位实物照片及核实的螺纹规格
- 站位人数 1/2/3、每人身高范围、目标互动区域的实际宽度
- 夜间有无雨水、冷凝、玻璃反射、投影漏光进入 RGB 画面

**拍摄权限：** 诊断图像只可在获得适当授权后在本地短时查看；默认不录制、不上传、不把儿童脸部样例提交到 Git。

## 18. V2 多人追踪架构（从首个 commit 就按此实现）

### 18.1 目标与阶段

- **MVP：** 单人姿态追踪 + 单个骷髅，所有数据结构使用 `persons[]`。
- **M6：** 双人识别、`track_id` 保持与两个骷髅独立同步；用跨越、遮挡、退出重入测试身份一致性。
- **M7：** 三人可选模式、角色自动排布、站位引导、遮挡/拥挤优雅降级、现场 1/2/3 人混合压力测试。
- 若相机有效视野不足、Windows/ARM 采集带宽不足或夜间画面差，**报告不可行条件，不得伪称三人达标**。

### 18.2 数据设计

- 在 Python 定义 `PoseFrame`：`version`, `frame_id`, `timestamp`, `persons: list[TrackedPerson]`。
- `TrackedPerson`：`track_id`, `tracking_state`, `confidence`, `landmarks[33]`, `events`, `bbox`（可选）。
- 为每个人维护独立运动滤波器、动作状态、`last_seen` 和置信度；不可跨 `track_id` 复用滤波器缓存。
- `PoseLandmarker` 设定 `num_poses` 可配置 (1/2/3)，**输出顺序不能作为身份 ID**。关联算法从可解释的简单方案开始（bbox 中心/IoU、人体中心距离、关键点相似度、速度预测、匈牙利匹配及门限），日志记录 ID 变化；极端遮挡/轨迹交叉时进入 `occluded` / 触发重分配策略。
- 首次识别时分配一个 session-only UUID；不可输出可识别儿童身份，不做面部识别。
- Unity 预置 3 个骷髅实例或使用对象池，基于稳定 `track_id` 绑定。单人模式大角色，2–3 人模式自动排布为左中右并保持视觉位置平稳，**禁止角色每帧按检测数组顺序互换**。
- 每人独立 `tracking_lost` 和动画淡出，正常退出后释放槽位；用户在多人模式中丢失不影响其他人的动画。
- 调试 UI 显示追踪标号、目标检测位置、单人置信度、延迟和有效人数。现场演示可隐藏调试 UI。

### 18.3 多人自动化测试（必须新增）

- 0→1→2→3→2→1→0 人增减序列，验证 Unity 生成/隐藏角色正确。
- 同帧返回姿态列表顺序打乱，稳定 ID 不应仅因排序变化而改变。
- 两个人并排、交叉、短暂部分遮挡、完全消失、重新进入；不要求遮挡后身份 100% 准确，但**不允许无提示将人 A 的动作串到人 B 骷髅**。
- 独立 `track_id` 的滤波状态隔离，丢包、延迟、旧帧处理和无效值防护。
- 三人情况下测各人关键点质量、实际推理 FPS、投影面积分配，以及相机全身覆盖率，保留实测报告。

## 19. V2 里程碑、目录与验收修改

原 M0–M5 仍保留，但修改验收顺序如下：

1. **M0：设备可用性门禁。** 先在树莓派 5 ARM64 上完成只读 USB/内核/SDK 诊断。允许 `v4l2` RGB 先行，**不允许假设旧 OpenNI2 可在 ARM64 成功读取 depth**。若真实摄像头不可用，mock 主链路照常推进并明确硬件阻塞。
2. **M1：Pi→PC 链路。** MockCamera 可稳定发送 JPEG、健康状态及帧序号；服务器 drop-old。
3. **M2：真实相机。** 必须从 Pi 端采集；先 RGB，后评估 depth。窗口开口环境夜间演示验证。
4. **M3：AI 姿态。** 协议按 `persons[]` 实现，但先运行 `num_poses:1`。设置 1/2/3 人模式开关及预置身份关联接口。
5. **M4：Unity。** 单人实时动作，Renderer 已是基于 `track_id` 的角色池，不能硬编码唯一骷髅全局实例。
6. **M5：投影。** 夜间真实窗口、反射膜、投影光串扰、屏幕镜像、儿童安全与断线恢复。
7. **M6：两人实时。** 至少双人并排、进出及交叉测试，达到项目定义的追踪可靠性验收。
8. **M7：三人可选。** 摄像头视场允许才开放三人；监控骨架串人率、遮挡后的恢复率和端到端延迟。

必须新增或调整目录：

```text
docs/SITE_SURVEY.md
  docs/CAMERA_MOUNTING_CHECKLIST.md
  docs/MULTIPERSON_ACCEPTANCE.md
  desktop/pose/identity_tracker.py
  desktop/pose/pose_schema.py
  desktop/tests/test_identity_tracker.py
  desktop/tests/test_multiperson_lifecycle.py
  unity/Assets/Scripts/Tracking/SkeletonPool.cs
  unity/Assets/Scripts/Tracking/TrackedPersonRegistry.cs
  unity/Assets/Scripts/Tracking/MultiPersonLayout.cs
```

### 配置示例（V2 增量，Agent 应合并到真实 YAML）

```yaml
pose:
  num_poses: 1  # 在 M6、M7 按实测依次启用 2、3
  max_persons: 3
  identity_tracking: true
  lost_track_timeout_ms: 1000
  matching_max_distance: 0.25  # 示例归一化阈值，需测量调参
rendering:
  max_skeletons: 3
  auto_layout: true
  fallback_to_single_person: true
site:
  camera_mount: open_window_tripod
  no_glass_or_film_between_camera_and_child: true
  outdoors_exposure_allowed: false
  children_tracking_area_m: [2.0, 3.0]  # 初测距离区间，非硬件保底规格
```

配置中 `max_persons:3` 是**产品目标上限，不保证实际场地能追踪 3 人**；`outdoors_exposure_allowed:false` 表示默认禁止无防护直接室外部署，不代表相机在室内透过开口朝外无法工作。

## 20. 验收与硬件阻塞分级

- `PASS`：有可复现命令、日志、实测 FPS 和运行环境说明，功能真实通过。
- `MOCK_PASS`：软件逻辑通过模拟测试，**不可**写成真实硬件通过。
- `BLOCKED_HARDWARE`：摄像头 Pi5 ARM64 驱动不可用、USB 或安装条件不足；写清证据与可选择的替代采集后端（例如 Pi5 支持的普通 UVC RGB 摄像头）。**仍然禁止绕过 Pi5。**
- `BLOCKED_SITE`：窗口光路被膜/玻璃遮挡、夜间光线不够、雨/凝露风险、多人超出视场或相互遮挡过重。
- `NOT_TESTED`：没有进入现场或设备不可访问；禁止推断为通过。

最后生成 `docs/VALIDATION_REPORT.md`，分别列出 **单人／双人／三人** 测试状态与边界条件；缺乏实测必须标记 `NOT_TESTED`。

## 21. 给 Cursor/Copilot 的启动命令（直接执行）

> 阅读本文件并遵守所有硬件、隐私和多人架构约束。请立即在当前仓库执行 M0 + M1：创建目录和测试，完成 Raspberry Pi 5 USB/SDK 只读探测脚本、MockCameraSource、Pi 到 RTX 主机的 WebSocket 帧传输和本地预览。然后建立 `persons[]` 协议、`track_id` 抽象、Unity SkeletonPool 占位实现，确保后续不需要重写通信架构。**没有实物或运行环境时，不要声称已验证摄像头或三人性能**。不得擅自下载不可信驱动、修改固件或要求把儿童影像上传云端。每一阶段实际运行测试，并报告 PASS / MOCK_PASS / BLOCKED_HARDWARE / BLOCKED_SITE / NOT_TESTED 与下一步。
