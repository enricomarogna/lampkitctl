import unittest
from lampkitctl import utils
from unittest.mock import patch


class TestUtils(unittest.TestCase):
    """
    Classe di test per le funzioni del modulo utils.py.
    Estende unittest.TestCase per usare i metodi di test integrati.
    """

    def test_check_package_found(self):
        """
        Verifica che check_package() restituisca True
        se il pacchetto simulato è trovato nel sistema.
        """
        with patch("shutil.which", return_value="/usr/bin/apache2"):
            # Simula che "apache2" sia installato → dovrebbe restituire True
            self.assertTrue(utils.check_package("apache2"))

    def test_check_package_not_found(self):
        """
        Verifica che check_package() restituisca False
        se il pacchetto simulato NON è trovato.
        """
        with patch("shutil.which", return_value=None):
            # Simula che "apache2" NON sia installato → dovrebbe restituire False
            self.assertFalse(utils.check_package("apache2"))

    def test_install_package_success(self):
        """
        Verifica che install_package() chiami correttamente
        apt-get update e apt-get install senza errori.
        """
        with patch("subprocess.run") as mock_run:
            # Simuliamo che ogni chiamata a subprocess.run vada a buon fine
            mock_run.return_value.returncode = 0

            # Chiamiamo la funzione vera
            utils.install_package("apache2")

            # Controlliamo che siano stati chiamati esattamente due comandi
            self.assertEqual(mock_run.call_count, 2)

    def test_install_package_failure(self):
        """
        Verifica che install_package() non esploda
        se subprocess.run solleva un errore.
        """
        with patch("subprocess.run", side_effect=Exception("Errore")):
            try:
                # La funzione dovrebbe gestire l'eccezione e NON farla propagare
                utils.install_package("apache2")
            except Exception:
                self.fail("install_package ha sollevato un'eccezione.")

