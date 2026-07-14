import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import curve_fit
from typing import Dict, List, Any

# Domain-knowledge fallbacks and defaults
WARMUP_DEFAULTS = {
    "SOFT": 1.0,
    "MEDIUM": 1.5,
    "HARD": 2.5,
    "INTERMEDIATE": 1.0,
    "WET": 0.5
}

WEATHER_PENALTY_DEFAULTS = {
    "DRY":  {"SOFT": 0.0, "MEDIUM": 0.0, "HARD": 0.0, "INTER": 4.0,  "WET": 10.0},
    "DAMP": {"SOFT": 6.0, "MEDIUM": 4.0, "HARD": 3.0, "INTER": 0.0,  "WET": 2.5},
    "WET":  {"SOFT": 15.0,"MEDIUM": 12.0,"HARD": 10.0,"INTER": 3.0,  "WET": 0.0}
}

def correct_for_fuel(
    laps: pd.DataFrame,
    total_laps: int,
    consumption_kg_per_lap: float = 1.9,
    sensitivity_s_per_kg: float = 0.033
) -> pd.DataFrame:
    """Subtract the fuel mass weight penalty from lap times."""
    df = laps.copy()
    df["laps_remaining"] = total_laps - df["LapNumber"]
    df["fuel_kg"] = df["laps_remaining"] * consumption_kg_per_lap
    df["fuel_effect"] = df["fuel_kg"] * sensitivity_s_per_kg
    df["LapTime_corrected"] = df["LapTime_s"] - df["fuel_effect"]
    return df

def piecewise_degradation(tyre_age: np.ndarray, base_deg: float, cliff_age: float, cliff_sev: float) -> np.ndarray:
    """Piecewise tire degradation model with linear phase and quadratic cliff."""
    gradual = base_deg * tyre_age
    cliff = cliff_sev * np.maximum(0, tyre_age - cliff_age) ** 2
    return gradual + cliff

def fit_degradation_curve(laps_for_compound: pd.DataFrame, compound: str) -> Dict[str, float]:
    """Fit the piecewise degradation model to normalized compound lap times."""
    # Filter for clean green-flag racing laps
    clean_laps = laps_for_compound[
        (laps_for_compound["TrackStatus"] == "1") & 
        (laps_for_compound["IsAccurate"] == True)
    ].copy()
    
    if len(clean_laps) < 15:
        # Fallback to defaults if data is insufficient
        return {
            "base_deg": 0.08 if compound == "SOFT" else 0.05 if compound == "MEDIUM" else 0.03,
            "cliff_age": 18.0 if compound == "SOFT" else 28.0 if compound == "MEDIUM" else 38.0,
            "cliff_severity": 0.35 if compound == "SOFT" else 0.30 if compound == "MEDIUM" else 0.25,
            "warmup_penalty": WARMUP_DEFAULTS.get(compound, 1.5)
        }
        
    # Driver-stint normalization to remove pace bias
    normalized_laps = []
    for _, group in clean_laps.groupby(["Driver", "Stint"]):
        if len(group) < 3:
            continue
        # Find stint baseline (use 5th percentile to guard against anomalies)
        baseline = group["LapTime_corrected"].quantile(0.05)
        group["deg"] = group["LapTime_corrected"] - baseline
        normalized_laps.append(group)
        
    if not normalized_laps:
        # Trigger fallback if no driver had enough clean laps in a stint
        return {
            "base_deg": 0.08 if compound == "SOFT" else 0.05 if compound == "MEDIUM" else 0.03,
            "cliff_age": 18.0 if compound == "SOFT" else 28.0 if compound == "MEDIUM" else 38.0,
            "cliff_severity": 0.35 if compound == "SOFT" else 0.30 if compound == "MEDIUM" else 0.25,
            "warmup_penalty": WARMUP_DEFAULTS.get(compound, 1.5)
        }
        
    df_norm = pd.concat(normalized_laps, ignore_index=True)
    
    # Group by TyreLife and compute median to reduce stochastic noise
    age_median = df_norm.groupby("TyreLife")["deg"].median().reset_index()
    
    # Fit the piecewise model
    # p0: [base_deg, cliff_age, cliff_severity]
    p0 = [0.05, 20.0, 0.2]
    bounds = ([0.0, 5.0, 0.0], [0.5, 45.0, 2.0])
    
    try:
        popt, _ = curve_fit(
            piecewise_degradation,
            age_median["TyreLife"].values,
            age_median["deg"].values,
            p0=p0,
            bounds=bounds,
            maxfev=10000
        )
        base_deg, cliff_age, cliff_sev = popt
    except Exception:
        # Graceful fallback to compound-specific defaults on fit failure
        base_deg = 0.08 if compound == "SOFT" else 0.05 if compound == "MEDIUM" else 0.03
        cliff_age = 18.0 if compound == "SOFT" else 28.0 if compound == "MEDIUM" else 38.0
        cliff_sev = 0.35 if compound == "SOFT" else 0.30 if compound == "MEDIUM" else 0.25

    return {
        "base_deg": round(float(base_deg), 4),
        "cliff_age": round(float(cliff_age), 1),
        "cliff_severity": round(float(cliff_sev), 4),
        "warmup_penalty": WARMUP_DEFAULTS.get(compound, 1.5)
    }

def estimate_pit_loss(session_laps: pd.DataFrame) -> List[float]:
    """
    Estimate pit lane time loss per stop by comparing pit-lap times to stint medians.
    """
    laps = session_laps.copy()
    laps["LapTime_s"] = laps["LapTime"].dt.total_seconds()
    
    pit_losses = []
    for driver in laps["Driver"].unique():
        d_laps = laps[laps["Driver"] == driver].copy()
        
        # We need consecutive stints to measure pit stops
        stints = sorted(d_laps["Stint"].dropna().unique())
        for stint_idx in range(len(stints) - 1):
            stint = stints[stint_idx]
            next_stint = stints[stint_idx + 1]
            
            s_laps = d_laps[d_laps["Stint"] == stint]
            s_next_laps = d_laps[d_laps["Stint"] == next_stint]
            
            # Require enough clean laps in both stints
            s_clean = s_laps[s_laps["TrackStatus"] == "1"]
            s_next_clean = s_next_laps[s_next_laps["TrackStatus"] == "1"]
            
            if len(s_clean) < 3 or len(s_next_clean) < 3:
                continue
                
            in_lap = s_laps.iloc[-1]
            out_lap = s_next_laps.iloc[0]
            
            # Reference paces on warm tires
            ref_in = s_clean.iloc[:-1]["LapTime_s"].median()
            ref_out = s_next_clean.iloc[1:4]["LapTime_s"].median()
            
            if (np.isnan(ref_in) or np.isnan(ref_out) or 
                np.isnan(in_lap["LapTime_s"]) or np.isnan(out_lap["LapTime_s"])):
                continue
                
            # Total pit-stop related loss = in_lap + out_lap excess
            total_loss = (in_lap["LapTime_s"] + out_lap["LapTime_s"]) - (ref_in + ref_out)
            
            # Hamilton serving 10s penalty (Silverstone 2021) or other outliers
            if total_loss < 10.0 or total_loss > 40.0:
                continue
                
            # Subtract compound warmup penalty to isolate baseline pit lane loss
            compound = out_lap["Compound"].upper()
            warmup = WARMUP_DEFAULTS.get(compound, 1.5)
            pit_loss = total_loss - warmup
            
            pit_losses.append(pit_loss)
            
    return pit_losses

def calibrate_circuit(
    circuit_name: str,
    circuit_fastf1_name: str,
    seasons: List[int],
    total_laps: int,
    raw_dir: str = "data/raw",
    processed_dir: str = "data/processed"
) -> None:
    """Master calibration pipeline for a single circuit."""
    from src.data.fetch import load_race_session, extract_lap_data, extract_weather_trace, extract_safety_car_trace
    
    print(f"\n--- Starting Calibration: {circuit_name.upper()} ---")
    
    all_laps = []
    sc_traces = []
    scenario_templates = []
    pit_losses_all = []
    
    for year in seasons:
        try:
            print(f"Loading {year} {circuit_fastf1_name}...")
            session = load_race_session(year, circuit_fastf1_name)
        except Exception as e:
            print(f"[WARNING] Failed to load {year} session: {e}. Skipping.")
            continue
            
        # Ingest laps
        laps = extract_lap_data(session)
        laps_corrected = correct_for_fuel(laps, total_laps)
        all_laps.append(laps_corrected)
        
        # Safety car trace
        sc_trace = extract_safety_car_trace(session)
        sc_traces.append(sc_trace)
        
        # Weather trace
        weather_trace = extract_weather_trace(session)
        
        # Combine weather & SC for scenarios
        template = weather_trace.merge(sc_trace, on="LapNumber")
        template["race_id"] = f"{year}_{circuit_name}"
        scenario_templates.append(template)
        
        # Pit loss calculation
        pit_losses_all.extend(estimate_pit_loss(session.laps))
        
    if not all_laps:
        print(f"[ERROR] No data ingested for {circuit_name}. Calibration aborted.")
        return
        
    combined_laps = pd.concat(all_laps, ignore_index=True)
    
    # Fit piecewise degradation curves per compound
    compounds_params = {}
    for compound in ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]:
        c_laps = combined_laps[combined_laps["Compound"] == compound]
        compounds_params[compound] = fit_degradation_curve(c_laps, compound)
        
    # Baseline pace: 5th percentile of fuel-corrected MEDIUM laps (stable benchmark)
    med_laps = combined_laps[combined_laps["Compound"] == "MEDIUM"]
    base_pace = float(med_laps["LapTime_corrected"].quantile(0.05)) if len(med_laps) > 0 else 90.0
    
    # Pit lane loss: median of all computed losses
    pit_loss = round(float(np.median(pit_losses_all)), 1) if pit_losses_all else 22.0
    
    # Safety Car Probability per lap
    total_laps_count = sum(len(t) for t in sc_traces)
    total_sc_laps = sum(t["sc_active"].sum() for t in sc_traces)
    sc_prob = round(float(total_sc_laps / total_laps_count), 4) if total_laps_count > 0 else 0.015
    
    # Output calibration document
    calibration = {
        "circuit": circuit_name,
        "total_laps": total_laps,
        "base_pace": round(base_pace, 2),
        "pit_loss": pit_loss,
        "noise_std": 0.20,
        "fuel": {
            "consumption_kg_per_lap": 1.9,
            "sensitivity_s_per_kg": 0.033
        },
        "compounds": compounds_params,
        "weather_compound_penalty": WEATHER_PENALTY_DEFAULTS,
        "safety_car_probability_per_lap": sc_prob,
        "safety_car_lap_time": 160.0
    }
    
    # Create output directory
    out_dir = Path(processed_dir) / circuit_name
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Write calibration.json
    with open(out_dir / "calibration.json", "w") as f:
        json.dump(calibration, f, indent=2)
        
    # Write scenarios.parquet
    scenarios_df = pd.concat(scenario_templates, ignore_index=True)
    scenarios_df.to_parquet(out_dir / "scenarios.parquet", index=False)
    
    print(f"[SUCCESS] Calibrated {circuit_name.upper()} successfully!")
    print(f"   Base Pace: {calibration['base_pace']}s, Pit Loss: {calibration['pit_loss']}s, SC Prob: {calibration['safety_car_probability_per_lap']}")
    print(f"   Saved calibration.json and scenarios.parquet ({len(scenarios_df)//total_laps} templates) to {out_dir}")
