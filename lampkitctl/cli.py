"""
cli.py

Modulo CLI di lampkitctl: verifica e installa i pacchetti base per l’ambiente LAMP.
"""

from .utils import check_package, install_package

REQUIRED_PACKAGES = {
    "apache2": "Apache Web Server",
    "mysql": "MySQL Server",
    "php": "PHP Interpreter"
}


def main():
    """
    Funzione principale del tool.

    Verifica la presenza dei pacchetti fondamentali per un ambiente LAMP
    (Apache, MySQL, PHP). Per ogni pacchetto mancante, propone
    l'installazione interattiva all'utente.
    """
    print("===================================")
    print("  LAMPKitCTL - Verifica Ambiente")
    print("===================================")

    for pkg, description in REQUIRED_PACKAGES.items():
        print(f"\n- {description}: ", end="")
        if check_package(pkg):
            print("✅ Installato")
        else:
            print("❌ Non trovato")
            risposta = input(f"Vuoi installare {description}? [Y/n]: ").strip().lower()
            if risposta in ["y", "yes", ""]:
                install_package(pkg)
            else:
                print(f"[!] {description} non sarà installato.")
