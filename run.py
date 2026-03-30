#!/usr/bin/env python3
import sys
import os

# Add the current directory to the path so that 'ui' can be found
sys.path.insert(0, os.path.dirname(__file__))

from ui.main import main

if __name__ == "__main__":
    main()