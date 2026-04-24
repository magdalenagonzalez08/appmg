import shutil
import os

def replicar_db():
    origen = "database.db"
    destino = "backup.db"

    if os.path.exists(origen):
        shutil.copyfile(origen, destino)