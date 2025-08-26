import importlib.util
spec = importlib.util.spec_from_file_location(
    'logging_utils', r'C:\Users\tygus\OneDrive\CDI\Rena\Python\MVA2\app\utils\logging_utils.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('OK', hasattr(mod, 'UserLogger'))
