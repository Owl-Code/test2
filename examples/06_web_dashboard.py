import sys
import os

# Insert workspace src/ folder to Python path for direct running
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from base_graph.visualization_server import start_server

if __name__ == "__main__":
    start_server(port=8000, open_browser=True)
