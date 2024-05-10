# %% imports
import sleap
from pathlib import Path
from datetime import datetime
import pandas as pd

# %% Global variables
sleap.disable_preallocation()  # This initializes the GPU and prevents TensorFlow from filling the entire GPU memory

# this folder should contain one centroid & centered instance model for each experimental session type
SLEAP_MODELS_PATH = Path("mazeSLEAP/models")

# which sleap model to use for processing video from each session type
SESSION_TYPE2SLEAP_MODEL_NAME = {
    "maze": "C57B6_BigMaze_Neuropixel-1",
    "open_field": "C57B6_OpenField_Neuropixel-1",
    "object_open_field_1": "C57B6_ObjectOpenField_Neuropixel-1",
    "object_open_field_2": "C57B6_ObjectOpenField_Neuropixel-1",
}

# raw and preprocessed data paths
VIDEO_PATH = Path("../data/raw_data/video")
SLEAP_PATH = Path("../data/preprocessed_data/SLEAP")

# %% Functions


def track_video(video_path, session_type, save_labels=True, return_labels=False):
    """ """
    # load video & inference model
    video = sleap.load_video(str(video_path), grayscale=True)
    sleap_predictor = load_sleap_predictor(session_type)
    # process video
    predictions = sleap_predictor.predict(video)
    # save results
    output_filename = ".".join(video_path.name.split(".")[:-1]) + ".predicted.h5"
    predictions.export(str(SLEAP_PATH / output_filename))
    if return_labels:
        return predictions


def load_sleap_predictor(session_type, batch_size=4):
    """
    Searches the models folder to find the correct models for a given session type and returns a sleap predictor object.

    Args
    - session_type: str, the type of session in your experiment (eg, maze, open_field etc.)
    """
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


def get_video_paths_df():
    """
    Returns a pd.Dataframe with data extracted from video filenames,
    (rows: sessions, columns: datetime, video_path, vidoe_sync_pulse_path).
    Will later match to pycontrol sessions with nearest datetime. Note some errors in
    the video filenames (wrong subject, wrong session type etc. havn't been fixed in the video files
    but datetimes should always line up so that is all we need).

    note session_types for obj vect sessions are just open_field in video filenames
    """
    all_video_files = [f.name for f in Path(VIDEO_PATH).iterdir() if f.suffix == ".mp4"]
    all_sync_pulse_files = [f.name for f in Path(VIDEO_PATH).iterdir() if f.suffix == ".csv"]
    video_paths_info = []
    for video_file in all_video_files:
        video_paths_info.append(
            {
                "subject_ID": video_file.split(".")[0],
                "datetime": datetime.strptime(video_file.split("_")[-1].split(".")[0], "%Y-%m-%d-%H%M%S"),
                "video_path": str(Path(VIDEO_PATH) / video_file),
            }
        )
    video_paths_df = pd.DataFrame(video_paths_info)
    return video_paths_df
