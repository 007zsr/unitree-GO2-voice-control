# Unitree Go2 真机前检查流程

第一版默认只能使用 mock 模式。真机测试必须有人看护，周围无障碍物，并且先通过以下步骤。

1. 修改 `configs/app.yaml` 与 `configs/go2.yaml`，同时设置 `robot_mode: go2` 和 `enable_real_robot: true`。
2. 在 `configs/go2.yaml` 填入实际连接网卡 `network_interface`，不要沿用示例网卡名。
3. 安装并验证 CycloneDDS、`unitree_sdk2_python`、numpy、opencv-python。
4. 运行 `.venv\Scripts\python.exe project_cli.py status` 或 `scripts/check/check_anbangtu_env.py`，确认 Python、麦克风、网络、后台进程权限等报告。
5. 运行 `.venv\Scripts\python.exe project_cli.py go2-check`，确认 SDK 连接和状态读取。
6. 可选运行 `.venv\Scripts\python.exe project_cli.py go2-check --stop-test`，只测试 `StopMove`。
7. 先在 mock 中运行 `.venv\Scripts\python.exe scripts/run/run_mock_demo.py`，确认急停和危险指令拒绝。
8. 真机上先测试 `停下`，再测试 `站起来`、`坐下`。
9. 最后测试 `向前走一秒`，确认低速、时长不超过配置上限、动作结束自动停止。

任一步失败都不要继续真机动作测试。第一版禁止低层电机控制、跳跃、翻滚、高速奔跑、扑击、攻击性动作和远程公网控制。
