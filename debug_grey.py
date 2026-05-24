import sys
import traceback

def hook(exc_type, exc_value, exc_traceback):
    with open("crash.log", "w") as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

sys.excepthook = hook

import main
