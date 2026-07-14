import yaml
from pathlib import Path
from src.data.fetch import init_fastf1_cache
from src.data.calibrate import calibrate_circuit

def main():
    # Load configuration
    config_path = Path("configs/circuits.yaml")
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Initialize FastF1 cache directory
    cache_dir = config.get("fastf1", {}).get("cache_dir", "data/raw")
    init_fastf1_cache(cache_dir)

    # Calibrate each configured circuit
    circuits = config.get("circuits", [])
    if not circuits:
        print("No circuits found in the configuration.")
        return

    print(f"Loaded {len(circuits)} circuits for ingestion and calibration.")
    
    for circuit_cfg in circuits:
        name = circuit_cfg["name"]
        fastf1_name = circuit_cfg["fastf1_name"]
        total_laps = circuit_cfg["total_laps"]
        seasons = circuit_cfg["seasons"]

        print(f"\n==========================================")
        print(f"Processing Circuit: {name.upper()} ({fastf1_name})")
        print(f"Seasons to Ingest: {seasons}")
        print(f"Total Laps: {total_laps}")
        print(f"==========================================")
        
        try:
            calibrate_circuit(
                circuit_name=name,
                circuit_fastf1_name=fastf1_name,
                seasons=seasons,
                total_laps=total_laps,
                raw_dir=cache_dir
            )
        except Exception as e:
            print(f"[ERROR] Failed to calibrate circuit {name}: {e}")

if __name__ == "__main__":
    main()
