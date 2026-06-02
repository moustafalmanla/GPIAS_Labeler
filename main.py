import sys
import os

# Add the directory containing the 'gpias_labeler' package to sys.path
# This makes 'gpias_labeler' discoverable for direct imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpias_labeler.Labeler_main import main


if __name__ == "__main__":
    main()
