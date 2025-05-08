@echo off
echo Starting ComfyUI via WSL...
wsl -d ComfyUI -e bash -c "cd /mnt/c/Users/felix/ml/ComfyUI && . /home/felix/miniconda3/etc/profile.d/conda.sh && conda activate comfy && python3 main.py; echo Script finished. Press any key to exit; read -n 1"
pause
echo Done.