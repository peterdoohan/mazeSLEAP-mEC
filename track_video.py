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
    output_filename = ".".join(video_path.name.split(".")[:-1]) + f".predicted_{datetime.now().isoformat()}.h5"
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
        rows: sessions,
        columns:
            subject_ID: str
            session_type: str (maze, open_field, etc..)
            datetime: datetime object
            video_path: str (relative path to raw video file)
            tracking_completed: bool (if sleap tracking has been performed on video from session)
    """
    all_video_files = [f.name for f in Path(VIDEO_PATH).iterdir() if f.suffix == ".mp4"]
    all_sleap_files = [f.name for f in Path(SLEAP_PATH).iterdir() if f.suffix == ".h5"]
    all_sleap_original_datetime_strings = [  # datetimes_strings of original videos predictions were made on
        f.split(".")[1].split("_")[-3] for f in all_sleap_files
    ]
    video_paths_info = []
    for video_file in all_video_files:
        session_type = video_file.split(".")[1].split("_")[:-1]
        session_type = session_type[0] if len(session_type) == 1 else "_".join(session_type)
        session_datetime_string = video_file.split("_")[-1].split(".")[0]
        tracking_completed = True if session_datetime_string in all_sleap_original_datetime_strings else False
        video_paths_info.append(
            {
                "subject_ID": video_file.split(".")[0],
                "session_type": session_type,
                "datetime": datetime.strptime(session_datetime_string, "%Y-%m-%d-%H%M%S"),
                "video_path": str(Path(VIDEO_PATH) / video_file),
                "tracking_completed": tracking_completed,
            }
        )
    video_paths_df = pd.DataFrame(video_paths_info)
    return video_paths_df
