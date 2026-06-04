from pathlib import Path
import pandas as pd

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    
    We use Path(__file__).resolve() to dynamically find where this script is,
    and then go up two levels (.parent.parent) to reach the root folder.
    This guarantees that the paths work on any computer without hardcoded paths.
    """
    return Path(__file__).resolve().parent.parent

def get_data_dir(dir_type: str = "raw") -> Path:
    """
    Returns the Path object pointing to data/raw or data/processed.
    Automatically creates the directory if it does not already exist.
    
    Parameters:
    -----------
    dir_type : str
        Either 'raw' or 'processed'. Defaults to 'raw'.
    """
    if dir_type not in ["raw", "processed"]:
        raise ValueError("dir_type must be either 'raw' or 'processed'")
    
    data_dir = get_project_root() / "data" / dir_type
    
    # mkdir(parents=True, exist_ok=True) automatically creates the folder
    # if it doesn't exist, and does nothing if it already exists.
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def load_csv(filename: str, dir_type: str = "raw") -> pd.DataFrame:
    """
    Loads a CSV dataset from the data directory into a pandas DataFrame.
    
    Parameters:
    -----------
    filename : str
        The name of the CSV file (e.g., 'mutual_funds.csv').
    dir_type : str
        The data folder type: 'raw' or 'processed'.
    """
    file_path = get_data_dir(dir_type) / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found at: {file_path}")
    
    # Load and return the CSV file as a pandas DataFrame (data table)
    return pd.read_csv(file_path)
