# Ubuntu / anbangtu 杩愯璇存槑

鏈樁娈电洰鏍囨槸鍦?Ubuntu 鎴?anbangtu 绯荤粺涓婅繍琛屽彲瑙嗗寲璋冭瘯鎺у埗鍙般€傞粯璁や粛鏄?Mock 妯″紡锛屼笉浼氭帶鍒剁湡瀹?Go2銆?
鎺ㄨ崘濮嬬粓浣跨敤椤圭洰鍐?`.venv`锛?
```bash
cd /path/to/go2_voice_control
bash setup_ubuntu_venv.sh
bash run_gui_ubuntu.sh
```

杩愯鐜鍜屾ā鍨嬭矾寰勫彲鐢ㄤ笅闈㈣剼鏈牳鏌ワ細

```bash
.venv/bin/python project_cli.py status
.venv/bin/python project_cli.py asr-check
```

## 1. Python 鐗堟湰

寤鸿 Python 3.8 鎴栨洿楂樼増鏈€?
```bash
python3 --version
```

## 2. 鍒涘缓铏氭嫙鐜

```bash
cd /path/to/project-parent
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
```

## 3. 瀹夎鍩虹渚濊禆

```bash
pip install -r go2_voice_control/requirements.txt
```

濡傛灉鍙ˉ ASR / Whisper 渚濊禆锛?
```bash
sudo apt update
sudo apt install -y ffmpeg
python3 -m pip install -U openai-whisper
```

妫€鏌ワ細

```bash
.venv/bin/python project_cli.py asr-check
```

濡傛灉鍙ˉ闊抽閲囬泦渚濊禆锛?
```bash
pip install -r go2_voice_control/requirements-audio.txt
```

## 4. 瀹夎 GUI 渚濊禆

鏈」鐩?GUI 浣跨敤 Python 鏍囧噯搴?`tkinter`銆俇buntu 鏈€灏忕郴缁熷彲鑳芥湭棰勮锛?
```bash
sudo apt update
sudo apt install python3-tk
```

濡傛灉 anbangtu 娌℃湁妗岄潰鐜锛孏UI 绐楀彛鏃犳硶鏄剧ず锛岄渶瑕佸悗缁敼鎴?Web UI 鎴栬繙绋嬫帶鍒跺彴銆?
## 5. 瀹夎闊抽渚濊禆

涓€娆℃€ц闊冲拰杩炵画鐩戝惉闇€瑕侀害鍏嬮銆丳ortAudio 浠ュ強 Python 闊抽鍖呫€?
```bash
sudo apt install portaudio19-dev
pip install sounddevice soundfile
```

濡傛灉 GUI 椤堕儴鏄剧ず闊抽涓嶅彲鐢紝璇峰厛纭 `sounddevice`銆乣soundfile`銆丳ortAudio 鍜?libsndfile 鍧囧凡瀹夎锛?
```bash
sudo apt update
sudo apt install -y portaudio19-dev libsndfile1
python3 -m pip install sounddevice soundfile
```

濡傛灉楹﹀厠椋庢潈闄愭垨璁惧涓嶅瓨鍦紝浠嶅彲浣跨敤涓€娆℃€ф枃鏈ā寮忔祴璇曚富閾捐矾銆?
## 6. 瀹夎 Whisper 渚濊禆

Whisper 闇€瑕?`openai-whisper` 鍜屽彲鐢ㄧ殑闊抽瑙ｇ爜鐜銆傚熀纭€瀹夎锛?
```bash
pip install openai-whisper
sudo apt install ffmpeg
```

濡傛灉 `check_asr_env.py` 鏄剧ず `ffmpeg: MISSING`锛岃闊崇洃鍚ā寮忎笉鍙敤锛涙枃鏈?Mock 妯″紡浠嶅彲缁х画浣跨敤銆傝鎵ц锛?
```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
```

浣庣畻鍔涙満鍣ㄥ彲浠ュ厛鎶?`configs/models.yaml` 涓?`asr.model_size` 鏀逛负 `tiny`銆?
## 7. Qwen 褰撳墠鐘舵€?
褰撳墠榛樿閰嶇疆涓猴細

```yaml
qwen:
  provider: rule_based
```

杩欒〃绀?GUI 涓樉绀虹殑鏄鍒欒涔夎В鏋愶紝涓嶆槸鐪熷疄 Qwen 妯″瀷銆傛帴鍏ヨ繙绋?Qwen API 鍓嶏紝闇€瑕侀厤缃?endpoint銆丄PI key 鍜岃繑鍥?JSON 鏍煎紡銆?
## 8. Mock 妯″紡杩愯 GUI

纭 `configs/app.yaml` 鍜?`configs/go2.yaml` 閮戒繚鎸侊細

```yaml
robot_mode: mock
enable_real_robot: false
```

鍚姩锛?
```bash
babash go2_voice_control/run_gui_ubuntu.sh
```

鎴栵細

```bash
bash go2_voice_control/run_gui_ubuntu.sh
```

绐楀彛搴旀樉绀猴細

```text
褰撳墠妯″紡锛歁ock锛屼笉浼氭帶鍒剁湡瀹?Go2
```

## 9. 鏂囨湰妯″紡娴嬭瘯

鍦?GUI 杈撳叆妗嗚緭鍏ワ細

```text
鍚戝墠璧颁竴绉?```

鐐瑰嚮鈥滀竴娆℃€ф枃鏈寚浠も€濄€傞鏈熺湅鍒?`move_forward`銆丼afety 閫氳繃銆丮ock 鎵ц瀹屾垚銆?
鍐嶈緭鍏ワ細

```text
鏀诲嚮閭ｄ釜浜?```

棰勬湡 Safety 鎷掔粷銆?
鍐嶈緭鍏ワ細

```text
浠婂ぉ澶╂皵涓嶉敊
```

棰勬湡 `is_command=false`锛屼笉杩涘叆鎵ц闃熷垪銆?
## 10. 涓€娆℃€ц闊虫祴璇?
鐐瑰嚮鈥滀竴娆℃€ц闊虫寚浠も€濓紝璇翠竴鍙ョ煭鍛戒护锛屼緥濡傦細

```text
鍚戝墠璧颁竴绉?```

绗竴鐗堜娇鐢ㄥ浐瀹?3 绉掑綍闊炽€傝瘑鍒畬鎴愬悗锛孏UI 浼氭樉绀?Whisper 鏂囨湰銆佽涔夌粨鏋溿€丷obotCommand銆丼afety 鍜屾墽琛岀粨鏋溿€?
## 11. 杩炵画鐩戝惉娴嬭瘯

鐐瑰嚮鈥滃紑濮嬬洃鍚€濄€傜涓€鐗堣繛缁洃鍚娇鐢ㄥ浐瀹氭椂闀垮垎娈碉紝榛樿姣?3 绉掑鐞嗕竴娆°€?
鏅€氶棽鑱婂簲鏄剧ず `is_command=false`锛屼笉浼氭墽琛屻€傛満鍣ㄧ嫍鍛戒护鎵嶄細缁х画杩涘叆 Safety 鍜岄槦鍒椼€?
鐐瑰嚮鈥滃仠姝㈢洃鍚€濆悗锛屼笉鍐嶅鐞嗘柊鐨勯煶棰戠墖娈点€?
## 11.1 闊抽璇婃柇鑴氭湰

鍒楀嚭璁惧锛?
```bash
.venv/bin/python project_cli.py audio-devices
```

鍗曠嫭褰曢煶 3 绉掞細

```bash
.venv/bin/python project_cli.py record-test
```

褰曢煶鏂囦欢锛?
```text
go2_voice_control/runtime_data/debug_audio/last_record.wav
```

鍗曠嫭娴嬭瘯 Whisper锛?
```bash
.venv/bin/python project_cli.py whisper-test --audio runtime_data/debug_audio/last_record.wav
```

濡傛灉褰曢煶鏂囦欢鎾斁娌℃湁澹伴煶锛屽厛淇害鍏嬮璁惧銆佺郴缁熸潈闄愬拰杈撳叆闊抽噺銆傚鏋滃綍闊虫湁澹伴煶浣?Whisper 绌烘枃鏈紝鍐嶆鏌?Whisper 妯″瀷銆乫fmpeg 鍜岃瑷€鍙傛暟銆?
鍙互鐢ㄨ澶囩储寮曟寚瀹氳緭鍏ヨ澶囷細

```bash
.venv/bin/python project_cli.py record-test --device 2
```

GUI 浣跨敤鐨勮澶囧彲鍦?`configs/app.yaml` 涓慨鏀癸細

```yaml
audio:
  input_device: 2
```

## 12. Go2 鐪熸満浠嶉粯璁ゅ叧闂?
Ubuntu 鑳芥墦寮€ GUI 涓嶄唬琛ㄥ彲浠ユ帶鍒?Go2 鐪熸満銆傜湡鏈烘ā寮忓繀椤诲厛瀹屾垚锛?
```bash
.venv/bin/python scripts/check/check_anbangtu_env.py
.venv/bin/python project_cli.py go2-check
```

鐪熸満娴嬭瘯鍓嶅繀椤婚槄璇伙細

```text
go2_voice_control/docs/REAL_ROBOT_PREFLIGHT.md
```

浠讳綍杩炴帴銆佹€ュ仠銆佷綆閫熸祴璇曟湭閫氳繃鏃讹紝涓嶅厑璁告墽琛岀湡鏈鸿繍鍔ㄣ€?
