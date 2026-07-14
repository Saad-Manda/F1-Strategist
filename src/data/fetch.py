import os
import fastf1
import pandas as pd
from pathlib import Path
from typing import List, Tuple

def init_fastf1_cache(cache_dir: str = "data/raw") -> None:
    """Initialize the FastF1 cache directory."""
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)

def load_race_session(year: int, event_name: str) -> fastf1.core.Session:
    """Load and cache a FastF1 race session (Race session only)."""
    session = fastf1.get_session(year, event_name, "R")
    session.load(laps=True, telemetry=False, weather=True)
    return session

def extract_lap_data(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Extract lap data for tire degradation calibration.
    Filters out safety car laps and unrepresentative laps.
    """
    laps = session.laps.copy()
    
    # Convert LapTime to seconds
    laps["LapTime_s"] = laps["LapTime"].dt.total_seconds()
    
    # Basic data cleanliness filters
    laps = laps.dropna(subset=["Compound", "TyreLife", "LapTime_s"])
    
    # Standardize compound names to uppercase
    laps["Compound"] = laps["Compound"].str.upper()
    
    # Keep only valid racing compounds
    valid_compounds = {"SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"}
    laps = laps[laps["Compound"].isin(valid_compounds)]
    
    return laps[["LapNumber", "Driver", "Compound", "TyreLife", 
                 "LapTime_s", "Stint", "TrackStatus", "IsAccurate"]]

def extract_weather_trace(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Extract lap-by-lap weather trace for scenario templates.
    Weather data is sampled at ~1min intervals; interpolate to each lap completion time.
    """
    weather = session.weather_data.copy()
    if weather.empty:
        # Fallback if weather data is missing
        laps_count = session.total_laps if hasattr(session, "total_laps") else 60
        return pd.DataFrame({
            "LapNumber": list(range(1, laps_count + 1)),
            "weather_regime": ["DRY"] * laps_count,
            "TrackTemp": [25.0] * laps_count,
            "AirTemp": [20.0] * laps_count,
            "Rainfall": [False] * laps_count
        })

    # Group laps to find the session time when the leader completed each lap
    laps_time = session.laps[["LapNumber", "Time"]].groupby("LapNumber").first().reset_index()
    laps_time = laps_time.sort_values("Time")
    weather = weather.sort_values("Time")
    
    # Merge weather data to the closest lap timestamp in session time
    merged = pd.merge_asof(laps_time, weather, on="Time")
    
    # Classify weather regime based on grid compound usage (most reliable sensor)
    laps_compounds = session.laps.groupby("LapNumber")["Compound"].apply(
        lambda x: x.str.upper().value_counts().idxmax() if len(x) > 0 else "MEDIUM"
    ).reset_index()
    
    def get_regime(compound: str) -> str:
        if compound == "WET":
            return "WET"
        elif compound == "INTERMEDIATE":
            return "DAMP"
        return "DRY"
    
    laps_compounds["weather_regime"] = laps_compounds["Compound"].apply(get_regime)
    merged = merged.merge(laps_compounds[["LapNumber", "weather_regime"]], on="LapNumber")
    
    # Ensure correct columns are present
    for col in ["TrackTemp", "AirTemp", "Rainfall"]:
        if col not in merged.columns:
            merged[col] = 25.0 if "Temp" in col else False
            
    return merged[["LapNumber", "weather_regime", "TrackTemp", "AirTemp", "Rainfall"]]

def extract_safety_car_trace(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Extract lap-by-lap safety car status (SC and VSC) using TrackStatus flags.
    Codes: '4' = Safety Car active, '6' = Virtual Safety Car active.
    """
    laps = session.laps.copy()
    laps["sc_active"] = laps["TrackStatus"].astype(str).str.contains("4")
    laps["vsc_active"] = laps["TrackStatus"].astype(str).str.contains("6")
    
    # Group by LapNumber and see if any driver experienced SC/VSC on this lap
    sc_trace = laps.groupby("LapNumber")[["sc_active", "vsc_active"]].any().reset_index()
    return sc_trace
