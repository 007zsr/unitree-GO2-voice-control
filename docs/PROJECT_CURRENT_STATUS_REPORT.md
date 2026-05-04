# go2_voice_control 当前项目完成情况报告

生成时间：2026-05-04  
核查方式：只读读取代码、配置、文档、已有日志和已有测试报告；未运行测试，未安装依赖，未下载模型，未执行 Go2 真机动作。  
重点文件核查：用户指定的重点文件均已找到；`docs/PROJECT_CURRENT_STATUS_REPORT.md` 为本次新生成报告。

## 1. 项目当前定位

当前项目是一个 Unitree Go2 语音控制软件原型，定位为 Windows 开发测试优先、Ubuntu / anbangtu 后续部署的 Mock-first 控制台。

当前默认配置为：

- `robot_mode: mock`
- `enable_real_robot: false`
- GUI / 输入 -> `SessionRuntime` -> ASR / NLU -> `RobotCommand` -> `SafetyController` -> `CommandQueue` -> Adapter
- 默认使用 `MockAdapter`，Go2 真机模式默认关闭

项目已经有 Go2 真机适配框架和真机前检查文档，但当前核查未发现真机运动已执行或语音直控真机已启用的证据。

## 2. 当前已完成的核心功能

已完成并有代码/日志证据的核心链路：

- GUI：已完成基础桌面控制台，可启动、显示状态、触发一次性文本/语音、连续监听、急停和设置。
- Audio capture：已接入 `sounddevice` / `soundfile`，支持一次性录音和连续监听滚动窗口。
- Whisper ASR：已接入 `openai-whisper`，配置为 `language: auto`，项目内存在 `models/whisper/base.pt`。
- NLU：当前以 `rule_based` / catalog alias / fuzzy rule 为主，Qwen remote/local 仅保留接口和配置。
- RobotCommand：已完成从语义结果到规范化命令的转换。
- CommandPlan：已支持单句多命令、最多 3 条、stop 截断后续命令。
- Safety：已完成置信度、危险语义、速度、时长、站立状态、真机开关等检查。
- CommandQueue：已完成队列执行和 stop 高优先级插队。
- MockAdapter：已可用，可模拟执行安全动作和 catalog 动作。
- Go2Adapter：已有 SDK 接入框架，但未验证真机。
- 日志系统：已完成 GUI session、one-shot、continuous、events、errors、batch test 等日志。

框架或未完成项：

- Qwen local：未真实启用，`models/qwen/` 仅有占位文件。
- Go2 真机控制：仅有框架和前置检查流程，未见真机运动验证。
- Ubuntu / anbangtu：有脚本和配置草案，未见实机部署成功报告。
- 完整离线便携：`models/whisper/base.pt` 已在项目内，但未找到 `wheelhouse/`，离线 Python 依赖包尚不完整。

## 3. 当前已完成的 GUI 功能

GUI 当前支持：

- 开始监听：已完成。
- 停止监听：已完成。
- 一次性语音指令：已完成，最近日志显示音频、Whisper、ffmpeg 可用。
- 一次性文本指令：已完成。
- 急停 stop：已完成，通过 `submit_emergency_stop()` 提交 `stop`。
- 设置面板：已完成，可设置 UI 语言、识别偏好、strict/relaxed、去重窗口和 cooldown。
- 日志显示：已完成，显示 UI log 和当前日志路径。
- ASR 结果显示：已完成，`ASR transcript` 和 ASR diagnostics 面板存在。
- NLU 结果显示：已完成，`Semantic result` 面板存在。
- CommandPlan 显示：已完成，`Command Plan` 面板存在。
- Safety 结果显示：已完成，`Safety decision` 面板存在。
- Mock 执行结果显示：已完成，`Execution result` / `PipelineDebugResult` 中显示 adapter result。
- Go2 官方动作列表筛选：部分完成，GUI 有 Supported commands 面板和 All/Safe/Caution/Dangerous/Disabled 筛选。

未完成或不能承诺：

- GUI 直接安全控制真机：未完成，且按规则不应默认允许。
- 真机运动状态可视化：未见已完成证据。

## 4. 当前已完成的语音识别功能

Whisper 状态：

- 已安装并可用。最新 GUI 日志显示 `whisper_available=true`、`whisper_loaded=true`、`whisper_executed=true`。
- Whisper 模型 `base.pt` 已存在于 `models/whisper/`。

ffmpeg 状态：

- 当前 Windows 环境可用，日志显示 `ffmpeg_available=true`，ffmpeg 来自系统 PATH。
- 这说明当前 Windows 可用，但 Ubuntu / anbangtu 仍需单独安装系统 ffmpeg。

麦克风采集状态：

- 当前可用。最新 GUI session 显示 audio status 可用，连续监听日志有 RMS / peak / sample rate / duration 诊断。

语言支持：

- 英文识别：已跑通，例如 `Stand up please.` -> `stand_up`。
- 中文识别：已跑通，例如 `向前走一秒` -> `move_forward`。
- 中英混合：已有日志和批量文本测试覆盖。

仍存在的问题：

- Whisper 仍可能误识别，尤其连续监听滚动窗口中的背景语音、长句或相邻片段。
- ASR 空文本仍会出现，最近两天 summary 合计 `ASR empty=14`；最新未汇总连续监听目录中也有 `asr_empty=3`。
- 当前已有 ASR 诊断日志，包含 no_speech_prob、RMS、peak、语言、segments preview、模型路径等。

## 5. 当前已完成的语义理解 / NLU 功能

当前 NLU 以 rule-based、catalog alias、fuzzy rule 为主：

- `configs/models.yaml` 中 `qwen.provider: rule_based`、`qwen.mode: rule_based`。
- GUI 最新日志显示 `Qwen mode: rule_based`。
- Qwen remote/local 调用代码存在，但当前未启用。

当前能识别的主要命令：

- `stand_up`
- `sit_down`
- `stand_down`
- `move_forward`
- `move_backward`
- `turn_left`
- `turn_right`
- `stop`
- `status_report`
- `unknown_relative_move`
- `dance1` / `dance2` 等 caution catalog 动作
- `front_flip` / `back_flip` / `left_flip` / `front_jump` / `hand_stand` 等 dangerous catalog 动作

语言支持：

- 支持中文。
- 支持英文。
- 支持中英混合；批量文本测试 `E_mixed_language` 为 20/20 完全正确。

限制：

- `Take a seat.` 当前漏识别为 `none`。
- `起来。` 当前漏识别为 `none`，但 `站起来。` 可以识别为 `stand_up`。
- Qwen local 不是当前真实 NLU 后端。

## 6. 当前已完成的 CommandPlan 连续指令功能

CommandPlan 当前支持：

- `turn right then turn left`
- `stand up then move forward`
- `sit down then stand up`
- 最多 3 条命令，超过会截断。
- `stop` 会截断后续命令。
- 连续监听支持按 plan signature 去重，但仍不是完全稳定。

最近日志/测试中的成功例子：

- `turn right and then turn left` -> `turn_right -> turn_left`
- `please turn right and then turn left` -> `turn_right -> turn_left`
- `stand up, turn right, turn left, sit down` -> `stand_up -> turn_right -> turn_left`，`truncated=true`
- `Sit down, sit down, sit down, sit down, sit down.` -> `sit_down -> sit_down -> sit_down`，`truncated=true`
- `turn right, then stop, then turn left` -> `turn_right -> stop`，后续 `turn_left` 被 stop 截断

当前注意点：

- 重复命令会被保留在计划中，最多保留 3 条，例如 `turn_right -> turn_right` 或 `sit_down -> sit_down -> sit_down`。
- 连续监听中已有 `duplicate_skipped` / `plans_skipped_duplicate`，说明去重在生效。
- 但 stop 不参与普通去重，最近日志中出现过 stop 连续执行 5 次。
- needs_confirmation 的 `come here` 类计划未提交执行，但可重复出现提示/拒绝。

## 7. 当前已完成的模糊指令识别功能

已支持并有测试/日志证据的模糊指令：

- `I am on your left, come here` -> `turn_left`
- `I am on your right, come here` -> `turn_right`
- `come here` / `Hello come here` -> `unknown_relative_move`，`needs_confirmation=true`，不自动前进

代码中已支持但日志未充分验证：

- `sleep a little bit` / `sleep` / `rest` -> `sit_down` 候选，confidence 约 0.65。
- 最新两天报告未找到 `sleep a little bit` 样例；批量 fixture 中也未看到 sleep/rest 样例。

当前模糊文本批量测试结果：

- 总测试数：260
- 完全正确：258
- 部分正确：2
- 严重错误：0
- 完全正确率：99.23%
- F/G 模糊与 come here 类样例完全正确率：100%

失败样例：

- `Take a seat.`：期望 `sit_down`，实际 `none`
- `起来。`：期望 `stand_up`，实际 `none`

## 8. 当前已完成的 Safety 安全系统

Safety 当前能处理：

- 机器人必须站立才能移动 / 转向。
- 危险动作默认禁用或拒绝。
- `come here` 不自动前进，缺少定位信息时进入 `unknown_relative_move` / confirmation。
- `stop` 最高优先级，不受普通去重阻挡。
- 真机模式默认关闭。
- 当前配置为 `robot_mode=mock`、`enable_real_robot=false`。

已见拒绝类型：

- `robot must be standing before this action`
- `duration 100.00s exceeds max 2.00s`
- `duration 3.00s exceeds max 2.00s`
- `speed level 'fast' is not allowed`
- `semantic result marked request as dangerous`
- `unknown_relative_move` 需要确认或不提交

Safety 拒绝当前已基本区分为正常控制结果，不应算系统错误。最近连续监听 summary 显示 `System errors: 0`，`Safety rejected` 单独统计。不过旧日志/早期报告中仍保留了一些历史错误记录，阅读时需要区分时间。

## 9. 当前已完成的 MockAdapter / Go2Adapter 状态

MockAdapter：

- 已可用。
- 能执行模拟 `stand_up`、`sit_down`、`stand_down`、`move_forward`、`move_backward`、`turn_left`、`turn_right`、`stop`、`status_report` 和 catalog 动作模拟。
- 最近两天报告显示 `Adapter failed=0`。

Go2Adapter：

- 已有框架。
- 代码中已导入 `unitree_sdk2py`、`SportClient`、`SportModeState_`，并实现 `StandUp`、`Sit` / `StandDown`、`Move`、`StopMove`、状态读取和 catalog SDK 方法调用。
- 但当前未见 SDK 已安装、Go2 已连接、真机状态读取成功或真机动作成功的日志证据。

必须明确回答：

- 当前是否执行过 Go2 真机动作：否。当前核查未发现执行过真机动作的证据。
- 当前是否允许语音直接控制真机：否。默认配置关闭，真机模式需要显式配置和前置检查。

## 10. 当前已完成的日志系统

日志目录已存在：

- `runtime_data/logs/gui_sessions/`
- `runtime_data/logs/one_shot/`
- `runtime_data/logs/continuous/`
- `runtime_data/logs/errors/`
- `runtime_data/logs/batch_text_tests/`
- `runtime_data/logs/events/`
- `runtime_data/logs/index/`

已支持：

- GUI session 日志：已完成。
- 一次性任务日志：已完成。
- 连续监听日志：已完成。
- CommandPlan 日志：已完成。
- Safety 拒绝日志：已完成。
- 测试报告日志：已完成。
- ASR 诊断日志：已完成。

当前日志问题：

- 早期 `latest_logs_report.md` 中指出 continuous summary 曾出现 error 计数重复问题。
- 最新 summary 中 `System errors: 0` / `Error count: 0` 已更清晰，但旧错误仍留在 `errors/`。
- 最新未结束/未汇总的连续监听目录 `listen_20260429_165936_e82c18` 有 `chunks.jsonl` / `commands.jsonl`，但未找到 `summary.md`，说明该 run 的 summary 生成不完整或未正常结束。

## 11. 当前已完成的模型与便携化管理

当前存在：

- `models/whisper/`：存在。
- `models/whisper/base.pt`：存在，大小约 145 MB。
- `models/qwen/`：存在，但仅有 `.gitkeep`，未发现真实 Qwen 本地模型。
- `.venv/`：存在，为 Windows 项目虚拟环境。
- `wheelhouse/`：未找到。
- `scripts/check/check_portable_project.py`：存在。
- `scripts/model_tools/collect_whisper_models.py`：存在。
- `scripts/model_tools/collect_qwen_models.py`：存在。

模型迁移状态：

- Whisper 模型已经在项目 `models/whisper/`。
- Qwen 模型未真实存在。
- 模型迁移报告显示曾扫描用户级 Whisper 缓存目录，源文件仍保留，但当前配置和日志均指向项目内 `models/whisper/`。
- 当前不再依赖用户级 Whisper 缓存来加载模型；ffmpeg 仍是系统依赖，不是项目内便携文件。

便携化结论：

- 可以复制源代码、配置、`models/whisper/` 到其他机器作为迁移基础。
- 不能直接把 Windows `.venv` 用于 Ubuntu / anbangtu，必须在目标系统重新创建虚拟环境。
- 未找到 `wheelhouse/`，因此不能承诺完整离线安装 Python 依赖。
- 最新 GUI 日志显示 `Portable status: OK`，但这个 OK 主要针对当前 Windows 项目路径、模型目录和 `.venv`。

## 12. 当前已完成的测试系统

当前测试类型包括：

- 单元测试：`tests/` 下有 66 个 `test_` 用例定义。
- GUI runtime bridge 测试。
- GUI audio unavailable / ASR unavailable 测试。
- ASR dependency 测试。
- Audio dependency / diagnostics 测试。
- Whisper 文件测试脚本。
- 连续监听设置与去重测试。
- 模糊文本批量测试。
- 危险动作测试。
- CommandPlan 测试。
- Go2 action catalog / scan parser 测试。

本次没有运行测试，因为任务要求只读核查。

已有测试报告：

- `docs/STRUCTURE_CLEANUP_REPORT.md` 记录过 `Ran 31 tests OK`，但这是历史结果，不能等同当前 66 个测试用例的最新执行结果。
- `runtime_data/logs/batch_text_tests/current/fuzzy_text_test_report.md` 是当前最完整的批量文本测试结果。

## 13. 已经修复过的重要问题

- 问题：`sounddevice` / `soundfile` 缺失。当前状态：已修复于当前 Windows 环境；早期错误仍留在历史日志。
- 问题：Whisper 未安装。当前状态：已修复，最新日志显示可用。
- 问题：ffmpeg 缺失。当前状态：已修复于当前 Windows 环境；Ubuntu / anbangtu 仍需单独安装。
- 问题：ASR 空文本无法诊断。当前状态：已修复，已有 RMS、peak、no_speech_prob、segments 等诊断。
- 问题：连续监听静音片段刷屏。当前状态：部分修复，已有 `skipped_silent` 和静音阈值；仍会记录静音/空文本统计。
- 问题：一次性语音和连续监听并发冲突。当前状态：已基本修复，GUI bridge 有 audio busy 防护。
- 问题：Whisper 模型路径混乱。当前状态：已修复，指向 `models/whisper`。
- 问题：C 盘模型缓存迁移。当前状态：已修复为复制项目内模型；源缓存未删除。
- 问题：日志系统缺失。当前状态：已修复。
- 问题：Safety 拒绝误记为 error。当前状态：已基本修复，新 summary 中 Safety 与 system error 分开；历史日志仍需区分。
- 问题：CommandPlan 不支持多命令。当前状态：已修复。
- 问题：`come here` 误执行风险。当前状态：已修复为 unknown / needs confirmation，不自动前进。
- 问题：危险动作分类缺失。当前状态：已修复，catalog 中已有 caution / dangerous / disabled 分类。

## 14. 当前仍存在的问题

- Whisper 仍可能误识别，尤其是连续监听滚动窗口和背景语音。
- strict 模式已降低误触发，但仍可能对含命令词的混合文本产生控制意图，需继续收紧触发条件。
- 普通闲聊误执行：批量文本测试为 0，但连续监听中“长片段含命令词”的风险仍存在。
- ASR 近似误识别：批量文本 `I_asr_near_misrecognition` 为 20/20，但真实 ASR 仍可能输出近似命令或危险词。
- `move_backward`：批量文本已有覆盖并通过；最近两天自然语音/连续监听日志未见充分覆盖。
- `sleep fuzzy`：代码支持 sleep/rest -> `sit_down` 候选，但当前日志和批量 fixture 未充分覆盖。
- CommandPlan 重复命令：会保留重复命令，最多 3 条；可能符合测试预期，但真实语音中有重复执行风险。
- 连续监听去重：已生效但不稳定；stop 不去重，needs_confirmation 类 `come here` 可重复出现。
- Qwen local：未启用。
- Go2 真机：未验证。
- Ubuntu / anbangtu：未实机部署。
- 最新 `listen_20260429_165936_e82c18` 没有 summary.md，连续监听 run 收尾/汇总仍需检查。

## 15. 当前测试结果汇总

模糊文本批量测试：

- 总测试数：260
- 完全正确：258
- 部分正确：2
- 严重错误：0
- 完全正确率：99.23%
- needs_confirmation 准确率：100%
- risk_level 准确率：99.23%
- 多 intent 样例解析准确率：100%
- F/G 模糊与 come here 样例完全正确率：100%

主要失败类别：

- 英文单命令别名：`Take a seat.` 漏识别。
- 中文单命令别名：`起来。` 漏识别。

连续监听汇总：

- 最近两天报告统计：Total chunks 337，ASR success 251，Commands 40，Plans detected 38，Safety rejected 11，Executed success 47，Adapter failed 0，System errors 0。
- 最新有 summary 的连续监听 `listen_20260429_155153_887db5`：Total chunks 43，ASR success 19，Commands 5，Plans executed 5，Safety rejected 8，System errors 0。
- 最新无 summary 的连续监听 `listen_20260429_165936_e82c18`：chunks 47，其中 `needs_confirmation=5`、`non_command=36`、`safety_rejected=1`、`asr_empty=3`、`skipped_silent=2`。

单元测试：

- 历史文档记录 `Ran 31 tests OK`。
- 当前 tests 目录已有 66 个 `test_` 用例定义。
- 本次未重新运行测试，不能承诺当前全量单元测试最新结果。

## 16. 当前不能承诺的功能

- 不能承诺真机安全运动已经验证。
- 不能承诺 Ubuntu / anbangtu 已部署成功。
- 不能承诺 Qwen 本地模型已经真实接入。
- 不能承诺所有官方 Go2 动作都可真机执行。
- 不能承诺 Whisper 识别永远准确。
- 不能承诺 `come here` 能自动走到主人身边。
- 不能承诺完整离线便携安装已完成，因为未找到 `wheelhouse/`。

## 17. 当前项目风险点

- 最大安全风险：连续监听误触发或重复触发，尤其是 stop、长句含命令词、ASR 误识别出的危险词或方向词。
- 最大交付风险：Go2 真机未验证，Mock 成功不等于真机可用。
- 最大部署风险：Ubuntu / anbangtu 未实机验证，Windows `.venv` 不可直接迁移。
- 最大 NLU 风险：当前以 rule-based 为主，Qwen local 未接入，复杂自然语言理解能力有限。
- 最大 ASR 风险：Whisper 在真实环境中仍会出现空文本、错词、语言混淆和滚动窗口切分问题。
- 最大日志风险：历史错误和当前状态混在同一日志目录，报告阅读时容易误判。

## 18. 下一阶段建议任务

优先级 1：修复模糊文本批量测试中的剩余错误，先补 `Take a seat.` 和 `起来。`。  
优先级 2：补齐普通闲聊误触发过滤，尤其连续监听中长句含命令词的情况。  
优先级 3：补齐 ASR 近似误识别过滤，并把真实 ASR 误识别样例加入 fixture。  
优先级 4：补齐 `move_backward` 自然语音/连续监听测试和 `sleep fuzzy` 测试。  
优先级 5：完善 Go2 官方动作库 GUI 展示，清楚区分 safe / caution / dangerous / disabled 与 mock/real 可用性。  
优先级 6：准备 Ubuntu / anbangtu 部署检查，不直接做真机运动。  
优先级 7：只读 Go2 连接检查，先验证 SDK、网卡、状态读取、StopMove 前置条件。  
优先级 8：真机低速动作测试前置流程，严格按 `docs/REAL_ROBOT_PREFLIGHT.md` 执行，不能跳过。

## 19. 当前可用命令与运行方式

Windows 常用命令：

```bat
setup_windows_venv.bat
run_gui_windows.bat
.venv\Scripts\python.exe project_cli.py status
.venv\Scripts\python.exe project_cli.py asr-check
.venv\Scripts\python.exe project_cli.py portable-check
.venv\Scripts\python.exe project_cli.py test
.venv\Scripts\python.exe project_cli.py fuzzy-text-test
.venv\Scripts\python.exe project_cli.py logs --last 5
.venv\Scripts\python.exe project_cli.py logs --errors
.venv\Scripts\python.exe project_cli.py audio-devices
.venv\Scripts\python.exe project_cli.py record-test
.venv\Scripts\python.exe project_cli.py whisper-test --audio runtime_data\debug_audio\last_record.wav
.venv\Scripts\python.exe project_cli.py collect-models
.venv\Scripts\python.exe project_cli.py go2-check
.venv\Scripts\python.exe project_cli.py scan-go2-actions
```

Ubuntu / anbangtu 常用命令：

```bash
bash setup_ubuntu_venv.sh
bash run_gui_ubuntu.sh
.venv/bin/python project_cli.py status
.venv/bin/python project_cli.py asr-check
.venv/bin/python project_cli.py portable-check
.venv/bin/python project_cli.py test
.venv/bin/python project_cli.py fuzzy-text-test
.venv/bin/python project_cli.py logs --last 5
.venv/bin/python project_cli.py logs --errors
.venv/bin/python project_cli.py audio-devices
.venv/bin/python project_cli.py record-test
.venv/bin/python project_cli.py whisper-test --audio runtime_data/debug_audio/last_record.wav
.venv/bin/python project_cli.py collect-models
.venv/bin/python project_cli.py go2-check
.venv/bin/python project_cli.py scan-go2-actions
```

注意：

- 本次未运行上述命令，只读取项目现状。
- `go2-check` 默认是连接/状态检查导向；当前配置为 mock，会拒绝真实 Go2 连接。
- `fuzzy-text-test` 在 `project_cli.py` 中存在，但 `docs/COMMANDS.md` 当前未列出，可后续补文档。

## 20. 总结结论

当前 `go2_voice_control` 已经是一个 Mock-first 的可用原型：GUI、一次性文本、一次性语音、连续监听、Whisper ASR、rule-based NLU、CommandPlan、Safety、CommandQueue、MockAdapter 和日志系统都有实际代码和日志证据。批量模糊文本测试表现较好，260 条中 258 条完全正确，严重错误为 0。

但当前还不能视为 Go2 真机可用版本。Qwen local 未启用，Go2Adapter 未真机验证，Ubuntu / anbangtu 未部署验证，连续监听仍有误触发/重复触发风险，ASR 仍可能误识别。下一阶段应继续在 Mock 和只读连接检查范围内收紧 NLU/ASR/Safety/日志，不应直接跳到真机运动。
