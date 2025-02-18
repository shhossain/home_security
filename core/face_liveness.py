from pathlib import Path
import cv2
import numpy as np
import onnxruntime
from PIL import Image
from torchvision import transforms as T
import urllib.request
from tqdm import tqdm


class LivenessDetection:
    def __init__(self, checkpoint_path: str):
        self.pbar = None
        if not Path(checkpoint_path).is_file():
            print("Downloading the DeepPixBiS onnx checkpoint:")
            urllib.request.urlretrieve(
                "https://github.com/ffletcherr/face-recognition-liveness/releases/download/v0.1/OULU_Protocol_2_model_0_0.onnx",
                Path(checkpoint_path).absolute().as_posix(),
                lambda block_num, block_size, total_size: show_progress(
                    self.pbar, block_num, block_size, total_size
                ),
            )
        self.deepPix = onnxruntime.InferenceSession(
            checkpoint_path, providers=["CPUExecutionProvider"]
        )
        self.trans = T.Compose(
            [
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def __call__(self, face_arr: np.ndarray) -> float:
        face_rgb = cv2.cvtColor(face_arr, cv2.COLOR_BGR2RGB)
        face_pil = Image.fromarray(face_rgb)
        face_tensor = self.trans(face_pil).unsqueeze(0).detach().cpu().numpy()  # type: ignore
        output_pixel, output_binary = self.deepPix.run(
            ["output_pixel", "output_binary"], {"input": face_tensor.astype(np.float32)}
        )
        liveness_score = (
            np.mean(output_pixel.flatten()) + np.mean(output_binary.flatten())
        ) / 2.0
        return liveness_score


def show_progress(pbar, block_num, block_size, total_size):
    if pbar is None:
        pbar = tqdm(total=total_size, unit="B", unit_scale=True)

    downloaded = block_num * block_size
    if downloaded < total_size:
        pbar.update(downloaded)
    else:
        pbar.close()
        pbar = None
