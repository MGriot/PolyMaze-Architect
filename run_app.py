import traceback
import sys
import os

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    import main
    main.main()
except Exception:
    traceback.print_exc()
