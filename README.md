# lampkitctl

Uno strumento CLI in Python per installare e configurare automaticamente un ambiente LAMP (Linux, Apache, MySQL, PHP) su macchine Ubuntu-based.

## 🔧 Funzionalità previste

- Verifica e installazione dei servizi LAMP
- Creazione VirtualHost Apache
- Aggiunta al file `/etc/hosts`
- Creazione cartelle web in `/var/www`
- Creazione database MySQL con utente dedicato
- Installazione automatica di WordPress (opzionale)

## 📦 Requisiti

- Python 3.8+
- Ubuntu 20.04 / 22.04 / 24.04
- Privilegi sudo

## 🚀 Esecuzione

```bash
python3 lampkitctl.py
