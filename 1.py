import psutil
from pathlib import Path
for proc in psutil.process_iter(attrs=['pid', 'name']):
    if 'v2rayN' in proc.info['name']:
         Path(proc.exe()).parent
