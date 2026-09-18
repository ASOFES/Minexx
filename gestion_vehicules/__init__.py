import os
import sys

# Ajouter le répertoire parent au PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importer les modules nécessaires
# from notifications.utils import notify_user, send_sms, send_whatsapp