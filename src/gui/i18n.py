from __future__ import annotations


TEXTS = {
    "en": {
        "app.title": "Go2 Voice Control Console",
        "button.start_listening": "Start listening",
        "button.stop_listening": "Stop listening",
        "button.one_shot_voice": "One-shot voice",
        "button.one_shot_text": "One-shot text",
        "button.emergency_stop": "Emergency stop",
        "button.clear_log": "Clear UI log",
        "button.settings": "Settings",
        "label.asr": "ASR transcript",
        "label.semantic": "Semantic result",
        "label.command_plan": "Command Plan",
        "label.command": "RobotCommand",
        "label.safety": "Safety decision",
        "label.execution": "Execution result",
        "label.asr_debug": "ASR diagnostics",
        "label.debug": "PipelineDebugResult",
        "label.log": "UI log",
        "label.commands": "Supported commands",
        "state.idle": "idle",
        "state.listening": "listening",
        "state.processing": "processing",
        "state.recording": "recording",
        "settings.title": "Settings",
        "settings.ui_language": "UI Language",
        "settings.recognition": "Recognition Preference",
        "settings.command_mode": "Command Detection Mode",
        "settings.dedup": "Deduplicate enabled",
        "settings.dedup_window": "Deduplicate window seconds",
        "settings.cooldown": "Same intent cooldown seconds",
        "settings.semantic_mode": "Semantic Understanding Mode",
        "settings.llm_enabled": "Enable Qwen / LLM fallback",
        "settings.llm_provider": "LLM Provider",
        "settings.local_model_dir": "Local model path",
        "settings.llm_min_conf": "Fallback min confidence",
        "settings.llm_timeout": "LLM timeout seconds",
        "settings.llm_tokens": "LLM max output tokens",
        "settings.llm_temperature": "LLM temperature",
        "settings.allow_remote_api": "Allow remote API providers",
        "settings.check_model": "Check Qwen model status",
        "settings.llm_safety_note": (
            "Qwen / LLM only assists semantic understanding. It never bypasses CommandPlan, "
            "SafetyController, CommandQueue, or adapter checks."
        ),
        "settings.save": "Save",
        "settings.cancel": "Cancel",
    },
    "zh": {
        "app.title": "Go2 语音控制台",
        "button.start_listening": "开始监听",
        "button.stop_listening": "停止监听",
        "button.one_shot_voice": "一次性语音",
        "button.one_shot_text": "一次性文本",
        "button.emergency_stop": "急停 stop",
        "button.clear_log": "清空日志",
        "button.settings": "设置",
        "label.asr": "语音识别结果",
        "label.semantic": "语义理解结果",
        "label.command_plan": "命令计划",
        "label.command": "标准化 RobotCommand",
        "label.safety": "安全判断",
        "label.execution": "执行结果",
        "label.asr_debug": "ASR 诊断",
        "label.debug": "PipelineDebugResult",
        "label.log": "界面日志",
        "label.commands": "当前可用命令",
        "state.idle": "未监听",
        "state.listening": "正在监听",
        "state.processing": "正在处理",
        "state.recording": "正在录音",
        "settings.title": "设置",
        "settings.ui_language": "界面语言",
        "settings.recognition": "识别偏好",
        "settings.command_mode": "命令检测模式",
        "settings.dedup": "开启去重",
        "settings.dedup_window": "去重窗口秒数",
        "settings.cooldown": "同动作冷却秒数",
        "settings.semantic_mode": "语义理解模式",
        "settings.llm_enabled": "启用 Qwen / LLM fallback",
        "settings.llm_provider": "LLM Provider",
        "settings.local_model_dir": "本地模型路径",
        "settings.llm_min_conf": "Fallback 最低置信度",
        "settings.llm_timeout": "LLM 超时时间秒数",
        "settings.llm_tokens": "LLM 最大输出 tokens",
        "settings.llm_temperature": "LLM temperature",
        "settings.allow_remote_api": "允许远程 API provider",
        "settings.check_model": "检查 Qwen 模型状态",
        "settings.llm_safety_note": "Qwen / LLM 只辅助语义理解，不会绕过 CommandPlan、SafetyController、CommandQueue 或 Adapter。",
        "settings.save": "保存",
        "settings.cancel": "取消",
    },
}


class I18n:
    def __init__(self, language: str = "en"):
        self.language = self.normalize_language(language)

    def set_language(self, language: str) -> None:
        self.language = self.normalize_language(language)

    def t(self, key: str) -> str:
        return TEXTS.get(self.language, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))

    def normalize_language(self, language: str) -> str:
        lowered = str(language or "en").lower()
        if lowered in {"zh", "cn", "chinese", "中文"}:
            return "zh"
        return "en"
