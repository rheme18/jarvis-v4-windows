import importlib
import pkgutil
from pathlib import Path

ACTIONS_REGISTRY = {}

def load_all_actions():
    """actions klasöründeki tüm geçerli .py dosyalarını dinamik olarak içe aktarır."""
    package_dir = Path(__file__).parent
    
    for _, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if is_pkg or module_name.startswith("_"):
            continue
            
        try:
            module = importlib.import_module(f"actions.{module_name}")
            ACTIONS_REGISTRY[module_name] = module
        except Exception as e:
            # Bağımlılığı eksik olan modülleri pas geçer, sistemi çökertmez
            print(f"[Klaus Action Loader] '{module_name}' yüklenemedi: {e}")

    return ACTIONS_REGISTRY

# Başlangıçta yükle
load_all_actions()