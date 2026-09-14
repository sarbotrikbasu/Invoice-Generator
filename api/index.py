import sys
import os

# Ensure workspace root is in python path for Vercel imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Vercel entrypoint
handler = app
