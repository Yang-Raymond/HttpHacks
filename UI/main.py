"""
Entry point for the Focus Timer application
"""
import sys
import os

# Add the appname directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'appname'))

from appname.app import main

if __name__ == "__main__":
    main()
