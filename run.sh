#!/bin/bash

# run.sh - Skrypt do łatwego uruchamiania systemu SKYNET-SAFE na różne sposoby
# Autor: Claude
# Data: 18.05.2025

# Wyświetlenie pomocy
show_help() {
    echo "SKYNET-SAFE - System uruchamiania"
    echo ""
    echo "Użycie: $0 [opcja]"
    echo ""
    echo "Opcje:"
    echo "  daemon       - Uruchamia system jako daemon w tle (platform=console)"
    echo "  interactive  - Uruchamia system w trybie interaktywnym"
    echo "  module       - Uruchamia bezpośrednio moduł główny"
    echo "  stop         - Zatrzymuje działającego daemona"
    echo "  status       - Sprawdza status działającego daemona"
    echo "  restart      - Restartuje daemona"
    echo ""
    echo "Przykłady:"
    echo "  $0 daemon      # Uruchamia jako daemon"
    echo "  $0 interactive # Uruchamia w trybie interaktywnym"
    echo "  $0 stop        # Zatrzymuje daemona"
}

# Sprawdzenie czy podano parametr
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Obsługa opcji
case "$1" in
    daemon)
        echo "Uruchamianie systemu jako daemon z konsolą..."
        python run_daemon.py start --platform console
        ;;
    interactive)
        echo "Uruchamianie systemu w trybie interaktywnym..."
        python run_interactive.py
        ;;
    module)
        echo "Uruchamianie głównego modułu..."
        python -m src.main
        ;;
    stop)
        echo "Zatrzymywanie daemona..."
        python run_daemon.py stop
        ;;
    status)
        echo "Sprawdzanie statusu daemona..."
        python run_daemon.py status
        ;;
    restart)
        echo "Restartowanie daemona..."
        python run_daemon.py restart
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo "Nieznana opcja: $1"
        show_help
        exit 1
        ;;
esac

exit 0