"""
utils.py

Funzioni di supporto per lampkitctl: gestione pacchetti e installazioni.
"""

import shutil
import subprocess


def check_package(package):
    """
    Verifica se un pacchetto è disponibile nel sistema.

    Args:
        package (str): Il nome del pacchetto/binary da cercare (es. 'apache2').

    Returns:
        bool: True se il pacchetto è installato, False altrimenti.
    """
    return shutil.which(package) is not None


def install_package(package):
    """
    Installa un pacchetto nel sistema utilizzando apt-get.

    Args:
        package (str): Il nome del pacchetto da installare (es. 'php').
    """
    print(f"\n[*] Installazione di {package}...")
    try:
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", package], check=True)
        print(f"[+] {package} installato con successo.")
    except subprocess.CalledProcessError:
        print(f"[!] Errore durante l'installazione di {package}.")
