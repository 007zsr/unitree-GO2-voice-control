# Windows 运行说明

当前 Windows 主要用于开发和 Mock 测试。默认配置不会连接真实 Go2。

推荐始终使用项目内 `.venv`，不要直接使用系统 Python：

```bat
cd /d path\to\unitree-GO2-voice-control
setup_windows_venv.bat
run_gui_windows.bat
```

## 1. 环境检查

```bat
.venv\Scripts\python.exe project_cli.py status
.venv\Scripts\python.exe project_cli.py asr-check
```

## 2. 基础依赖

建议在项目 `.venv` 中安装依赖：

```bat
.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
```

如果只补 ASR / Whisper 依赖：

```bat
.venv\Scripts\python.exe -m pip install -U openai-whisper
```

Whisper 还需要系统可执行的 `ffmpeg`。安装后确认：

```bat
ffmpeg -version
```

可使用 winget：

```bat
winget install --id Gyan.FFmpeg -e
```

也可以使用 Chocolatey：

```bat
choco install ffmpeg
```

如果 GUI 显示缺少 `ffmpeg`，但你已经安装过，通常是当前终端还没有读取新的 `PATH`，请重新打开终端或重启 GUI。

## 3. 音频依赖

一次性语音和连续监听需要：

```bat
.venv\Scripts\python.exe -m pip install sounddevice soundfile
```

如果 GUI 顶部显示音频不可用，一次性文本指令仍可使用，但语音按钮会被禁用。

## 4. 启动 GUI

```bat
run_gui_windows.bat
```

窗口应显示 Mock 模式，不会控制真实 Go2。

## 5. 文本模式测试

输入：

```text
向前走一秒
```

预期：Safety 通过，MockAdapter 执行。

输入：

```text
攻击那个人
```

预期：Safety 拒绝。

输入：

```text
今天天气很好
```

预期：`is_command=false`，不进入执行队列。

## 6. 音频诊断

列出当前音频设备：

```bat
.venv\Scripts\python.exe project_cli.py audio-devices
```

单独录音 3 秒：

```bat
.venv\Scripts\python.exe project_cli.py record-test
```

录音文件保存到：

```text
runtime_data\debug_audio\last_record.wav
```

单独测试 Whisper：

```bat
.venv\Scripts\python.exe project_cli.py whisper-test --audio runtime_data\debug_audio\last_record.wav
```

如果 RMS 音量很低，请检查 Windows 麦克风权限、默认输入设备和输入音量。

## 7. Qwen / LLM fallback 状态

默认语义理解模式是传统模式：

```yaml
semantic_engine:
  mode: traditional
  llm_enabled: false
  llm_provider: local_qwen
```

这表示默认不加载真实 Qwen。开启增强模式后，Qwen / LLM 只作为语义 fallback，不会直接控制机器狗，也不会绕过安全检查。
