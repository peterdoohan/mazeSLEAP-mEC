# %% imports
import sleap

sleap.disable_preallocation()  # This initializes the GPU and prevents TensorFlow from filling the entire GPU memory

from pathlib import Path

# %% Global variables

# this folder should contain one centroid & centered instance model for each experimental session type
SLEAP_MODELS_PATH = Path("mazeSLEAP/models")

# which sleap model to use for processing video from each session type
SESSION_TYPE2SLEAP_MODEL_NAME = {
    "maze": "C57B6_BigMaze_Neuropixel-1",
    "open_field": "C57B6_OpenField_Neuropixel-1",
    "object_open_field_1": "C57B6_ObjectOpenField_Neuropixel-1",
    "object_open_field_2": "C57B6_ObjectOpenField_Neuropixel-1",
}

RAW_VIDEO_PATH = Path("../data/raw_data/video")

OUTPUT_SLEAP_PATH = Path("../data/preprocessed_data/SLEAP")

# %% Functions


def track_video(video_path, session_type, save_labels=True, return_labels=False):
    """ """
    # load video & inference model
    video = sleap.load_video(str(video_path))
    sleap_predictor = load_sleap_predictor(session_type)
    # process video
    predictions = sleap_predictor.predict(video)
    # save results
    output_filename = ".".join(video_path.name.split(".")[:-1]) + ".predicted.h5"
    predictions.export(str(OUTPUT_SLEAP_PATH / output_filename))
    if return_labels:
        return predictions


def load_sleap_predictor(session_type, batch_size=4):
    """ """
    all_model_paths = [p for p in SLEAP_MODELS_PATH.iterdir() if p.is_dir()]
    model_types = ["centroid", "centered_instance"]
    model_paths = []
    for model_type in model_types:
        model_path = [
            p
            for p in all_model_paths
            if p.name.split(".")[0] == SESSION_TYPE2SLEAP_MODEL_NAME[session_type]
            and p.name.split(".")[2] == model_type
        ]
        if len(model_path) != 1:
            raise FileNotFoundError(
                f"Check there is only one centroid and one centered instance model for session type {session_type} in {SLEAP_MODELS_PATH}"
            )
        else:
            model_path = model_paths.append(str(model_path[0]))
    sleap_predictor = sleap.load_model(
        model_paths, batch_size=batch_size, tracker="flow", tracker_max_instances=1, max_instances=1
    )
    return sleap_predictor
