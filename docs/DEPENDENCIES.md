# Dependencies

The project keeps dependency manifests in the repository root for low-risk setup
script compatibility.

- `requirements.txt`: shared Python dependencies.
- `requirements-audio.txt`: microphone capture dependencies.
- `requirements-asr.txt`: Whisper ASR dependency.
- `requirements-windows.txt`: Windows project environment.
- `requirements-ubuntu.txt`: Ubuntu project environment.

Windows setup:

```bat
setup_windows_venv.bat
```

Ubuntu setup:

```bash
sudo apt update
sudo apt install -y ffmpeg portaudio19-dev libsndfile1 python3-venv python3-tk
bash setup_ubuntu_venv.sh
```

The current GUI uses Tkinter. `PySide6` is still listed as a pending dependency
for a possible richer GUI path and should be reviewed before the first release.
