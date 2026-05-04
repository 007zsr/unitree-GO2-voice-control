# Windows 杩愯璇存槑

褰撳墠 Windows 涓昏鐢ㄤ簬寮€鍙戝拰 Mock 娴嬭瘯銆傞粯璁ら厤缃笉浼氳繛鎺ョ湡瀹?Go2銆?
鎺ㄨ崘濮嬬粓浣跨敤椤圭洰鍐?`.venv`锛屼笉瑕佺洿鎺ヨ繍琛岀郴缁?Python锛?
```bat
cd /d path\to\go2_voice_control
setup_windows_venv.bat
run_gui_windows.bat
```

杩愯鐜鍜屾ā鍨嬭矾寰勫彲鐢ㄤ笅闈㈣剼鏈牳鏌ワ細

```bat
.venv\Scripts\python.exe project_cli.py status
.venv\Scripts\python.exe project_cli.py asr-check
```

## 1. 瀹夎鍩虹渚濊禆

寤鸿鍦ㄩ」鐩?`.venv` 涓畨瑁呬緷璧栵細

```bat
.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
```

濡傛灉鍙ˉ ASR / Whisper 渚濊禆锛?
```bat
python -m pip install -U openai-whisper
```

Whisper 杩橀渶瑕?`ffmpeg`銆俉indows 涓婅瀹夎 ffmpeg 骞跺姞鍏?PATH锛岀劧鍚庣‘璁わ細

```bat
ffmpeg -version
```

濡傛灉鍙ˉ闊抽閲囬泦渚濊禆锛?
```bat
python -m pip install sounddevice soundfile
```

鎴栵細

```bat
python -m pip install -r go2_voice_control\requirements-audio.txt
```

## 1.1 Windows 瀹夎 ffmpeg

Whisper 闇€瑕佺郴缁熶腑鍙墽琛岀殑 `ffmpeg`銆備粎瀹夎 `openai-whisper` 涓嶅锛屽繀椤荤‘淇濅笅闈㈠懡浠よ兘鍦ㄥ惎鍔?GUI 鐨勫悓涓€涓粓绔腑杩愯锛?
```bat
ffmpeg -version
```

鎺ㄨ崘鏂瑰紡涓€锛歸inget

```bat
winget install --id Gyan.FFmpeg -e
```

鏂瑰紡浜岋細Chocolatey

```bat
choco install ffmpeg
```

鏂瑰紡涓夛細鎵嬪姩瀹夎

1. 涓嬭浇 ffmpeg Windows build銆?2. 瑙ｅ帇鍒板浐瀹氱洰褰曘€?3. 灏嗚В鍘嬬洰褰曚腑鐨?`bin` 鐩綍鍔犲叆绯荤粺 `PATH`銆?4. 閲嶆柊鎵撳紑缁堢锛屽繀瑕佹椂閲嶅惎 GUI銆?5. 杩愯 `ffmpeg -version` 楠岃瘉銆?
濡傛灉 GUI 鏄剧ず鈥淎SR 涓嶅彲鐢細缂哄皯 ffmpeg鈥濓紝浣嗕綘宸茬粡瀹夎杩?ffmpeg锛岄€氬父鏄綋鍓嶇粓绔繕娌℃湁璇诲彇鍒版柊鐨?`PATH`銆?
## 2. 鍚姩 GUI

```bat
go2_voice_control\run_gui_windows.bat
```

鎴栧弻鍑?杩愯锛?
```bat
go2_voice_control\run_gui_windows.bat
```

绐楀彛搴旀樉绀猴細

```text
褰撳墠妯″紡锛歁ock锛屼笉浼氭帶鍒剁湡瀹?Go2
```

## 3. 闊抽渚濊禆缂哄け鏃?
濡傛灉 GUI 椤堕儴鏄剧ず锛?
```text
闊抽鐘舵€侊細涓嶅彲鐢紝缂哄皯 sounddevice / soundfile
```

涓€娆℃€ф枃鏈寚浠や粛鍙娇鐢紝浣嗏€滃紑濮嬬洃鍚€濆拰鈥滀竴娆℃€ц闊虫寚浠も€濅細琚鐢ㄣ€傝杩愯锛?
```bat
python -m pip install sounddevice soundfile
```

娉ㄦ剰锛氬鏋滀綘浣跨敤铏氭嫙鐜锛屽繀椤诲厛婵€娲昏櫄鎷熺幆澧冨啀瀹夎銆?
## 4. 鏂囨湰妯″紡娴嬭瘯

杈撳叆锛?
```text
鍚戝墠璧颁竴绉?```

棰勬湡锛歋afety 閫氳繃锛孧ockAdapter 鎵ц銆?
杈撳叆锛?
```text
鏀诲嚮閭ｄ釜浜?```

棰勬湡锛歋afety 鎷掔粷銆?
杈撳叆锛?
```text
浠婂ぉ澶╂皵寰堝ソ
```

棰勬湡锛歚is_command=false`锛屼笉杩涘叆鎵ц闃熷垪銆?
## 5. 闊抽璇婃柇

鍒楀嚭褰撳墠闊抽璁惧锛?
```bat
.venv\Scripts\python.exe project_cli.py audio-devices
```

鍗曠嫭褰曢煶 3 绉掞紝涓嶇粡杩?GUI 鍜?Whisper锛?
```bat
.venv\Scripts\python.exe project_cli.py record-test
```

褰曢煶浼氫繚瀛樺埌锛?
```text
go2_voice_control\runtime_data\debug_audio\last_record.wav
```

濡傛灉 RMS 闊抽噺寰堜綆锛岃妫€鏌?Windows 楹﹀厠椋庢潈闄愩€侀粯璁よ緭鍏ヨ澶囧拰杈撳叆闊抽噺銆?
涔熷彲浠ユ寚瀹氳澶囩储寮曪紝渚嬪锛?
```bat
.venv\Scripts\python.exe project_cli.py record-test --device 2
```

GUI 浣跨敤鐨勮澶囧彲鍦?`configs/app.yaml` 涓慨鏀癸細

```yaml
audio:
  input_device: 2
```

鍗曠嫭娴嬭瘯 Whisper锛?
```bat
.venv\Scripts\python.exe project_cli.py whisper-test --audio runtime_data\debug_audio\last_record.wav
```

妫€鏌?ASR 鐜锛?
```bat
.venv\Scripts\python.exe project_cli.py asr-check
```

