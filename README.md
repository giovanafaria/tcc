# Evacuation Simulation

Agent-based evacuation simulator for landslides and floods in favelas, considering people with disabilities (PwD).

## Features
- PwD agents with reduced mobility and visual differentiation
- Shapefile integration: reads path geometries and favor cells on these paths
- Terrain slope affecting agent speed
- A* pathfinding
- Interactive Mesa visualization

## How to Run
```bash
pip install -r requirements.txt
python -m src.utils.obstacle_mask
python -m src.utils.landslide_mask
python -m src.run
```

### How to Run in batch
```bash
python -m src.run_batch --runs x --active_areas 0 1 2
```

#### To run without simulating landslides
```bash
python -m src.run_batch -n x --disable-landslide
```
*PS:* x = the number of times you want to run the simulation, and the numbers in the active areas represent the risk areas
