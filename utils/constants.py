from pathlib import Path
import tempfile
import os
import stat
from multiprocessing import Value

# File permissions
DIR_PERMS = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO  # 0777
FILE_PERMS = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH  # 0644


def create_dir_with_perms(path: Path):
    path.mkdir(exist_ok=True)
    os.chmod(path, DIR_PERMS)


app_name = "face_security"
home_path = Path.home()
app_path = home_path / app_name
create_dir_with_perms(app_path)

data_path = app_path / "data"
create_dir_with_perms(data_path)

checkpoints = data_path / "checkpoints"
create_dir_with_perms(checkpoints)

img_folder = data_path / "imgs"
create_dir_with_perms(img_folder)

deepPix_checkpoint_path = checkpoints / "OULU_Protocol_2_model_0_0.onnx"

em_path = data_path / "embeddings"
create_dir_with_perms(em_path)

temp_dir = Path(tempfile.gettempdir()) / "face_security"
create_dir_with_perms(temp_dir)

current_frame_path = temp_dir / "current_frame.jpg"
frame_lock_path = temp_dir / "frame.lock"

# Set initial permissions for frame files if they exist
for file_path in [current_frame_path, frame_lock_path]:
    if file_path.exists():
        os.chmod(file_path, FILE_PERMS)


# process video feed
should_process_video = Value("b", False)
should_process_video.value = True

