import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')

print('=== Testing model registry with real weights ===')
from ml.inference.model_registry import load_all_models, get_load_status, all_models_loaded
load_all_models('ml/weights')

status = get_load_status()
print()
print('Load status:')
for k, v in sorted(status.items()):
    result = 'OK' if v else 'FAILED'
    print(f'  {k}: {result}')
print()
print('All loaded:', all_models_loaded())
