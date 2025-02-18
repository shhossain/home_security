from pathlib import Path

app_name = "face_security"
home_path = Path.home()
app_path = home_path / app_name
app_path.mkdir(parents=True, exist_ok=True)

data_path = app_path / "data"
data_path.mkdir(exist_ok=True)

checkpoints = data_path / "checkpoints"
checkpoints.mkdir(exist_ok=True)

img_folder = data_path / "imgs"
img_folder.mkdir(exist_ok=True)

deepPix_checkpoint_path = checkpoints / "OULU_Protocol_2_model_0_0.onnx"

em_path = data_path / "embeddings"
em_path.mkdir(exist_ok=True)

current_frame_path = data_path / "current_frame.jpg"
