#!/usr/bin/env python
import argparse
from src.model.simulation import EvacuationModel

def main():
    parser = argparse.ArgumentParser(
        description="Run the EvacuationModel multiple times headless"
    )
    parser.add_argument(
        "-n", "--runs",
        type=int,
        required=True,
        help="Number of simulation runs"
    )
    parser.add_argument(
        "--width", type=int, default=110,
        help="Grid width"
    )
    parser.add_argument(
        "--height", type=int, default=90,
        help="Grid height"
    )
    parser.add_argument(
        "--num_agents", type=int, default=20,
        help="Number of agents per run"
    )
    parser.add_argument(
        "--pwd_ratio", type=float, default=0.089,  # data from IBGE 
        help="Ratio of PWD agents"
    )
    parser.add_argument(
        "--active_areas", "-a",
        type=int,
        nargs="+",
        default=None,
        help="Which landslide mask indices to activate (e.g. 0 2 for areas 1 & 3)"
    )
    args = parser.parse_args()

    for i in range(1, args.runs + 1):
        print(f"\n=== Starting run {i} of {args.runs} ===")
        model = EvacuationModel(
            width=args.width,
            height=args.height,
            num_agents=args.num_agents,
            pwd_ratio=args.pwd_ratio,
            active_areas=args.active_areas
        )
        model.run_model()
    print("\nAll done!")

if __name__ == "__main__":
    main()
