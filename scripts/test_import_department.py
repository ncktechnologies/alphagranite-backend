import importlib
import traceback
try:
    mod = importlib.import_module('src.app.service.department')
    print('Imported department service OK')
except Exception:
    traceback.print_exc()
