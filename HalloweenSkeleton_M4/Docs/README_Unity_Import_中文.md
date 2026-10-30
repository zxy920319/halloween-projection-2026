# Halloween Skeleton · Milestone 4 交付说明

## 本包与你上传的代码的对应关系

- 现有 `PoseWebSocketClient.cs` 与 `PoseReceiver.cs` **原样保留**。当前客户端默认连接 `ws://127.0.0.1:8766/poses`。
- 现有 `PoseModels.cs` 定义 `PoseFrame.persons[]`、`TrackedPerson.track_id` 与 33 个 `PoseLandmark`。
- 现有 `SkeletonPool.cs` 是三个 `skeletonRoots` 的对象池，但原本只调用 `SkeletonDrawer.Draw()`。
- 本包 `Unity/SkeletonPool.cs` 为**替换版**：优先调用 `SkeletonPoseDriver`，否则继续调用原来的 `SkeletonDrawer`。
- `TrackedPersonRegistry.cs`、`MultiPersonLayout.cs`、`ConfidenceSmoother.cs` 不需要修改。

## 先说明交付物的性质

`Blender/generate_halloween_skeleton.py` 是 **真正生成 Blender Armature + 蒙皮权重** 的脚本。每个网格部件由对应骨骼以 100% 权重驱动；不是静态 OBJ，也不是只有关节示意线。形状为程序化拟写实恐怖骷髅原型，非高精度扫描资产。生成的骨骼包含 Hips、Spine、Chest、Neck、Head、Jaw、双臂、双腿、手脚和基础手指。

当前交付环境没有 Blender 可执行程序，因此**没有声称已经输出或实际检验 .fbx/.blend/.glb**；请在本机运行下面命令生成，检查导出日志与 Unity Rig 映射。

## 1. 使用 Blender 生成实际模型文件

建议 Blender 4.x（也兼容不少 3.6 环境）。安装 Blender 后：

**Windows PowerShell：**

```powershell
& "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" --background --python .\Blender\generate_halloween_skeleton.py -- --out "$PWD\Generated"
```

根据实际安装版本替换 `Blender 4.5` 路径。若 `blender` 已在 PATH：

```bash
blender --background --python Blender/generate_halloween_skeleton.py -- --out ./Generated
```

输出目标：

```text
Generated/
├── HalloweenSkeleton.blend
├── HalloweenSkeleton.fbx
└── HalloweenSkeleton.glb
```

Blender FBX/GLTF 导出功能随版本及插件可用性不同。请查看终端 `FBX exported` 和 `Finished` 日志。若 FBX 导出失败，先打开 `.blend` 在 Blender 中手动 File → Export → FBX。

## 2. 在 Blender 里检查是否真正绑定了骨骼

1. 打开 `HalloweenSkeleton.blend`。
2. Outliner 里应有 `HalloweenSkeleton_Rig`（Armature）及 `HalloweenSkeleton_SkinnedMesh`。
3. 选中 Armature，切换 **Pose Mode**，旋转 `LeftUpperArm`：上臂骨头的可见几何应当跟着旋转。
4. 旋转 `LeftLowerLeg`，检查小腿及脚的父骨骼变换。
5. 可见网格有 `Armature_Skin` modifier，并存在对应的 Vertex Groups。
6. Mesh 的每块骨头采用刚性权重，所以关节之间不会出现软体弯曲；这是骨骼骷髅原型的预期效果。

## 3. Unity 导入

1. 将 `Generated/HalloweenSkeleton.fbx` 拖到 `Assets/Models/`。
2. Inspector → **Rig** → 首先选 **Generic** → Apply。这里使用自定义骨名与控制器，最可靠。
3. 如果需要 Humanoid Avatar，再尝试 `Humanoid` → Configure 并检查必需骨骼，切勿将 Humanoid 成功当作前置假设。FBX 骨架、T-pose、肩骨、手指映射可能需要手动校正。
4. 在场景中实例化 FBX，将它放在一个空物体 `SkeletonCharacter_0` 下面；场景中可见角色应正对摄像机。根据 FBX 坐标导入结果旋转根物体，不要手动旋转每个骨骼。
5. 把 `Unity/SkeletonPoseDriver.cs` 加入 `Assets/Scripts/Tracking`。
6. 在 `SkeletonCharacter_0` 上添加 `SkeletonPoseDriver`，`Rig Root` 指向包含骨骼 Transform 的导入实例。如果不指定，会尝试从本对象的全部子物体里找骨骼。
7. **不要同时添加会改写骨骼的 Animator**，否则可能覆盖该原型驱动。
8. 复制两份 `SkeletonCharacter_0` 为 `_1` 和 `_2`。三个根物体都要有 SkeletonPoseDriver。
9. **用本包** `Unity/SkeletonPool.cs` **替换你原来的同名文件**，不要保留两个同名类定义。
10. 将 `SkeletonPool` Inspector 的 `skeletonRoots` 数组设置为 3，并拖入 3 个角色根物体。
11. `PoseReceiver` Inspector 的 `skeletonPool` 指向场景里的 `SkeletonPool`；`PoseWebSocketClient` Inspector 的 `receiver` 指向 `PoseReceiver`。
12. 运行姿态发布服务与 Unity Play，确认收到 `version=1,type="pose",persons=[...]` 消息。

### 角色与投影的建议参数

- 正交摄像机（Orthographic）正对角色，背景设纯黑，允许后续镜像校正。
- 肢体关节检测：`minVisibility=0.5` 作为起点；在暗光下可临时调低。
- Unity 输出目标 60 FPS；先验证 1 人，再逐步增加到 3 人。
- 角色摆位由现有 `MultiPersonLayout` 决定，摄像头里的人物交换顺序时仍须测试 `track_id` 的稳定性。

## 4. 原型动作控制的明确限制（重要）

本包 `SkeletonPoseDriver` 是 **2.5D 起步驱动**：使用 MediaPipe **normalized-image** 的 x/y 关键点方向控制上/下臂、上/下腿和躯干。没有 3D 摄像机标定、没有全身 IK、没有脚部锁定、也没有头部姿态求解。对于真实三维人物、遮挡、镜像、转身、复杂蹲下，不能称作 production 级 retargeter。

`ApplyPose` 接口暂未使用 `coordinate_space`、`units` 和 `z`；你的 PoseFrame 里虽有这些字段，但若服务器实际发送 **world space** 坐标而非 normalized image，必须先实现正确的坐标转换，再启用该驱动。

**下一里程碑建议：** 定义稳定的人体局部坐标系；按躯干方向将人体重定向到角色；求解骨盆姿态；Two-Bone IK 与脚部锁定；对遮挡使用置信度与姿态保持；对 3 人分别维护状态和滤波缓存。

## 5. 快速验收

- [ ] Blender 生成文件成功（日志没有 `FBX exporter failed`）
- [ ] Pose Mode 旋转手臂 / 小腿，几何随骨架而动
- [ ] Unity 项目中 C# 无编译错误
- [ ] 场景 1 人的数据能驱动 1 个真实 3D 骷髅（不是线条）
- [ ] 2/3 人分别对应不同角色且角色位置正确
- [ ] 观察是否需要对摄像机画面或模型做左右镜像（切换 `mirrorInput`）
- [ ] 断线 / 人物离场角色恢复隐藏状态

## 6. 常见故障

- **FBX 导入以后没有骨骼：** 优先用 Blender 检查 Armature 是否包含在导出选择里；导出时 Mesh 与 Armature 都必须选中。
- **`bound 0/9`：** FBX 导入时骨骼名称改变/嵌套不对；在 Unity Hierarchy 查看名称是否仍为 `LeftUpperArm` 等。
- **角色不动但线框动：** 检查是否替换了 `SkeletonPool.cs`，以及 prefab 是否挂载 SkeletonPoseDriver。
- **角色动作颠倒：** 检查姿态输入是否镜像、模型朝向和摄像机是否正对。
- **追踪抖动：** 本脚本只做基础旋转插值，需进一步做 per-track landmark 平滑与遮挡保持。
- **不同 Unity 版本 FBX 表现不同：** 先设 Generic，核对所有 Transform 名称，再尝试 Humanoid。

## 7. 给 Cursor 的下一步指令

> 阅读本目录 `Docs/README_Unity_Import_中文.md`、附件中原来的 `PoseModels.cs`、`PoseReceiver.cs`、`SkeletonPool.cs` 与本包代码。在不修改 WebSocket 协议的前提下，将真实 Blender 骷髅接入现有三人 SkeletonPool。先在本机 Blender 中执行脚本导出 FBX 并检查 Rig/权重，再在 Unity 中编译、加载 FBX 和测试 1 人、2 人、3 人的动作。若无法运行 Blender 或 Unity，必须明确写明未验证，不要虚构测试结果。
