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
python run.py
