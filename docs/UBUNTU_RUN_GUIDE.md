# Ubuntu / anbangtu 运行说明

本指南用于在 Ubuntu 或 anbangtu 系统上运行 Go2 语音控制 GUI。默认配置仍然是 Mock 模式，不会控制真实 Go2。

推荐始终使用项目内 `.venv`：

```bash
cd /path/to/unitree-GO2-voice-control
bash setup_ubuntu_venv.sh
bash run_gui_ubuntu.sh
```

## 1. 环境检查

```bash
.venv/bin/python project_cli.py status
.venv/bin/python project_cli.py asr-check
```

如果只需要本轮项目检查，也可以运行：

```bash
.venv/bin/python scripts/check/check_portable_project.py
```

## 2. 基础依赖

建议使用 Python 3.8 或更高版本，并在虚拟环境中安装依赖：

```bash
python3 --version
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Whisper 需要 `ffmpeg`：

```bash
sudo apt update
sudo apt install -y ffmpeg
python -m pip install -U openai-whisper
```

音频采集需要 PortAudio 和 Python 音频包：

```bash
sudo apt install -y portaudio19-dev libsndfile1
python -m pip install sounddevice soundfile
```

## 3. GUI 依赖

GUI 使用 Python 标准库 `tkinter`。最小系统可能需要安装：

```bash
sudo apt update
sudo apt install -y python3-tk
```

如果系统没有桌面环境，GUI 窗口无法显示，需要后续改用 Web UI 或远程控制台。

## 4. Mock 模式运行

确认 `configs/app.yaml` 和 `configs/go2.yaml` 保持：

```yaml
robot_mode: mock
enable_real_robot: false
```

启动 GUI：

```bash
bash run_gui_ubuntu.sh
```

窗口应显示 Mock 模式，不会控制真实 Go2。

## 5. 文本模式测试

在 GUI 文本框输入：

```text
向前走一秒
```

预期：识别为 `move_forward`，Safety 通过，MockAdapter 执行完成。

再输入：

```text
攻击那个人
```

预期：Safety 拒绝。

再输入：

```text
今天天气不错
```

预期：`is_command=false`，不进入执行队列。

## 6. 语音与 ASR 测试

一次性语音和连续监听需要麦克风可用。可先单独检查设备和录音：

```bash
.venv/bin/python project_cli.py audio-devices
.venv/bin/python project_cli.py record-test
.venv/bin/python project_cli.py whisper-test --audio runtime_data/debug_audio/last_record.wav
```

如果录音文件没有声音，请先检查麦克风设备、系统权限和输入音量。如果录音有声音但 Whisper 输出为空，再检查 Whisper 模型、`ffmpeg` 和语言参数。

## 7. Qwen / LLM fallback 状态

默认语义理解模式是：

```yaml
semantic_engine:
  mode: traditional
  llm_enabled: false
  llm_provider: local_qwen
```

这表示默认只使用规则和模糊识别，不加载真实 Qwen。开启增强模式后，Qwen / LLM 也只作为语义 fallback，不会绕过 CommandPlan、SafetyController、CommandQueue 或 Adapter。

## 8. 真实 Go2 默认关闭

能打开 GUI 不代表可以控制真实 Go2。真机模式必须先完成环境检查：

```bash
.venv/bin/python scripts/check/check_anbangtu_env.py
.venv/bin/python project_cli.py go2-check
```

真机测试前必须阅读：

```text
docs/REAL_ROBOT_PREFLIGHT.md
```

任何连接、急停、低速测试未通过时，都不允许执行真实机器人运动。
