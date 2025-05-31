#!/usr/bin/env python
import argparse
import multiprocessing
import os
# Make sure the paths to your modules are correct
from src.model.simulation import EvacuationModel
from src.utils.pathfinding import load_paths # Import load_paths

# This function will be executed by each parallel process
def run_single_simulation(run_id, model_params_dict, preloaded_path_mask_data): # Added preloaded_path_mask_data
    print(f"=== Starting Run {run_id} (Process ID: {os.getpid()}) ===")

    model = EvacuationModel(
        width=model_params_dict['width'],
        height=model_params_dict['height'],
        num_agents=model_params_dict['num_agents'],
        pwd_ratio=model_params_dict['pwd_ratio'],
        active_areas=model_params_dict['active_areas'],
        enable_landslide=model_params_dict['enable_landslide'],
        initial_path_mask=preloaded_path_mask_data # Pass the pre-loaded data here
    )
    model.run_model()
    print(f"--- Finished Run {run_id} (Process ID: {os.getpid()}) ---")
    return f"Run {run_id} completed."

def main():
    parser = argparse.ArgumentParser(
        description="Run the EvacuationModel multiple times headless, potentially in parallel"
    )
    parser.add_argument(
        "-n", "--runs",
        type=int, required=True,
        help="Number of simulation runs"
    )
    parser.add_argument(
        "--width", type=int,
        default=220, help="Grid width"
    )
    parser.add_argument(
        "--height", type=int,
        default=180,
        help="Grid height"
    )
    parser.add_argument(
        "--num_agents", type=int,
        default=480,
        help="Number of agents per run"
    )
    parser.add_argument(
        "--pwd_ratio", type=float,
        default=0.089,
        help="Ratio of PWD agents"
    )
    parser.add_argument(
        "--active_areas", "-a",
        type=int, nargs="+",
        default=None,
        help="Which landslide mask indices to activate (e.g. 0 2 for areas 1 & 3)"
    )
    parser.add_argument(
        "--enable-landslide",
        dest="enable_landslide",
        action="store_true",
        help="Enable landslide (default)"
    )
    parser.add_argument(
        "--disable-landslide",
        dest="enable_landslide",
        action="store_false",
        help="Disable landslide"
    )
    parser.add_argument(
        "--cores", type=int,
        default=None,
        help="Number of CPU cores to use (default: all available - 1)"
    )
    parser.set_defaults(
        enable_landslide=True
    )
    args = parser.parse_args()

    # --- Pre-load the path_mask ONCE in the main process ---
    print("Loading path mask data once for all runs...")
    shapefile_path_for_mask = "data/raw/Caminho.shp" # Make sure this path is correct
    try:
        # Use the width and height from args for consistency
        preloaded_path_mask = load_paths(args.width, args.height, shapefile_path_for_mask)
        print("Path mask loaded successfully.")
    except Exception as e:
        print(f"FATAL: Could not load path_mask data in main process: {e}")
        print("Please ensure the Shapefile path is correct and the file is not corrupted.")
        return # Exit if essential data can't be loaded
    # --- End of pre-loading ---

    if args.cores is None:
        num_cores_to_use = max(1, multiprocessing.cpu_count() - 1)
    else:
        num_cores_to_use = args.cores
    
    print(f"Running {args.runs} simulations using up to {num_cores_to_use} CPU core(s) in parallel.")

    run_arguments_list = []
    for i in range(1, args.runs + 1):
        current_model_params = {
            'width': args.width,
            'height': args.height,
            'num_agents': args.num_agents,
            'pwd_ratio': args.pwd_ratio,
            'active_areas': args.active_areas,
            'enable_landslide': args.enable_landslide,
        }
        # Add the preloaded_path_mask to the arguments for each run
        run_arguments_list.append((i, current_model_params, preloaded_path_mask))

    with multiprocessing.Pool(processes=num_cores_to_use) as pool:
        results = pool.starmap(run_single_simulation, run_arguments_list)

    print("\n--- Batch Run Summary ---")
    for res in results:
        print(res)
    
    print("\nAll batch simulation runs completed!")

if __name__ == "__main__":
    # This is important for multiprocessing on some OSes like Windows
    multiprocessing.freeze_support() 
    main()