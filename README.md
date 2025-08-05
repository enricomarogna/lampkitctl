# lampkitctl

Uno strumento CLI in Python per installare e configurare automaticamente un ambiente LAMP (Linux, Apache, MySQL, PHP) su macchine Ubuntu-based.

## 🔁 Clonazione del progetto

```bash
git clone git@github.com:enricomarogna/lampkitctl.git
cd lampkitctl
```

## 🔧 Funzionalità previste

* Verifica e installazione dei servizi LAMP
* Creazione VirtualHost Apache
* Aggiunta al file `/etc/hosts`
* Creazione cartelle web in `/var/www`
* Creazione database MySQL con utente dedicato
* Installazione automatica di WordPress (opzionale)

## 📦 Requisiti

* Python 3.8+
* Ubuntu 20.04 / 22.04 / 24.04
* Privilegi sudo

## 🚀 Esecuzione

Dal root del progetto:

```bash
python3 main.py
```

Oppure, dopo installazione come pacchetto, sarà possibile usare:

```bash
lampkitctl
```

> La CLI globale sarà disponibile dopo aver configurato `setup.py` con l’entry point.
