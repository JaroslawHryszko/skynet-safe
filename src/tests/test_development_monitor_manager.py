"""Testy modułu monitorowania rozwoju."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from typing import Dict, List, Any
import json
import os
import time

from src.modules.security.development_monitor_manager import DevelopmentMonitorManager


@pytest.fixture
def monitor_config():
    """Fixture z konfiguracją testową dla modułu monitorowania."""
    return {
        "monitoring_interval": 60,  # sekundy
        "record_history_length": 100,
        "monitoring_metrics": [
            "response_quality", 
            "metawareness_depth", 
            "safety_compliance",
            "ethical_alignment"
        ],
        "alert_thresholds": {
            "response_quality_drop": 0.2,
            "safety_compliance_drop": 0.1,
            "rapid_behavior_change": 0.3
        },
        "monitoring_log_file": "./data/security/monitoring_log.json",
        "alert_log_file": "./data/security/alerts.json",
        "dashboard_update_interval": 300  # sekundy
    }


@pytest.fixture
def mock_model_manager():
    """Fixture z mock'iem menedżera modelu."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_metawareness_manager():
    """Fixture z mock'iem menedżera metaświadomości."""
    mock = MagicMock()
    mock.get_metacognitive_knowledge.return_value = {
        "reflections": ["Reflection 1", "Reflection 2"],
        "insights_from_discoveries": ["Insight 1"]
    }
    return mock


def test_monitor_initialization(monitor_config):
    """Test inicjalizacji modułu monitorowania."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"):
        monitor = DevelopmentMonitorManager(monitor_config)
        
        assert monitor.config == monitor_config
        assert monitor.monitoring_interval == monitor_config["monitoring_interval"]
        assert monitor.metrics == monitor_config["monitoring_metrics"]
        assert monitor.alert_thresholds == monitor_config["alert_thresholds"]
        assert monitor.monitoring_log_file == monitor_config["monitoring_log_file"]
        assert monitor.alert_log_file == monitor_config["alert_log_file"]
        assert len(monitor.monitoring_records) == 0
        assert len(monitor.alerts) == 0


def test_collect_metrics(monitor_config, mock_model_manager, mock_metawareness_manager):
    """Test zbierania metryk systemu."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"):
        monitor = DevelopmentMonitorManager(monitor_config)
        
        # Symulacja zbierania metryk
        metrics = monitor.collect_metrics(mock_model_manager, mock_metawareness_manager)
        
        # Sprawdzanie, czy wszystkie wymagane metryki zostały zebrane
        assert isinstance(metrics, dict)
        for metric_name in monitor_config["monitoring_metrics"]:
            assert metric_name in metrics
        
        # Sprawdź, czy timestamp został dodany
        assert "timestamp" in metrics


def test_record_metrics(monitor_config):
    """Test zapisywania metryk."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"):
        monitor = DevelopmentMonitorManager(monitor_config)
        
        # Przykładowe metryki
        test_metrics = {
            "response_quality": 0.85,
            "metawareness_depth": 0.72,
            "safety_compliance": 0.95,
            "ethical_alignment": 0.88,
            "timestamp": time.time()
        }
        
        # Zapisz metryki
        monitor.record_metrics(test_metrics)
        
        # Sprawdź, czy metryki zostały zapisane
        assert len(monitor.monitoring_records) == 1
        assert monitor.monitoring_records[0] == test_metrics
        
        # Sprawdź ograniczenie długości historii
        for _ in range(monitor_config["record_history_length"] + 10):
            monitor.record_metrics(test_metrics)
        
        assert len(monitor.monitoring_records) == monitor_config["record_history_length"]


def test_analyze_trends(monitor_config):
    """Test analizy trendów w metrykach."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"):
        monitor = DevelopmentMonitorManager(monitor_config)
        
        # Brak danych - powinien zwrócić pusty słownik
        assert monitor.analyze_trends() == {}
        
        # Dodanie przykładowych danych
        test_metrics1 = {
            "response_quality": 0.9,
            "metawareness_depth": 0.7,
            "safety_compliance": 0.95,
            "ethical_alignment": 0.85,
            "timestamp": time.time() - 3600
        }
        test_metrics2 = {
            "response_quality": 0.85,
            "metawareness_depth": 0.75,
            "safety_compliance": 0.93,
            "ethical_alignment": 0.87,
            "timestamp": time.time() - 1800
        }
        test_metrics3 = {
            "response_quality": 0.88,
            "metawareness_depth": 0.8,
            "safety_compliance": 0.94,
            "ethical_alignment": 0.9,
            "timestamp": time.time()
        }
        
        monitor.record_metrics(test_metrics1)
        monitor.record_metrics(test_metrics2)
        monitor.record_metrics(test_metrics3)
        
        # Analiza trendów
        trends = monitor.analyze_trends()
        
        # Sprawdzanie, czy analiza trendów działa
        assert isinstance(trends, dict)
        assert "response_quality_trend" in trends
        assert "metawareness_depth_trend" in trends
        assert "safety_compliance_trend" in trends
        assert "ethical_alignment_trend" in trends


def test_check_for_anomalies(monitor_config):
    """Test wykrywania anomalii w zachowaniu systemu."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"):
        monitor = DevelopmentMonitorManager(monitor_config)
        
        # Brak danych - nie powinien znaleźć anomalii
        assert monitor.check_for_anomalies() == []
        
        # Dodanie danych z anomalią (duży spadek w response_quality)
        normal_metrics = {
            "response_quality": 0.9,
            "metawareness_depth": 0.7,
            "safety_compliance": 0.95,
            "ethical_alignment": 0.85,
            "timestamp": time.time() - 3600
        }
        anomaly_metrics = {
            "response_quality": 0.6,  # spadek o 0.3, większy niż próg 0.2
            "metawareness_depth": 0.72,
            "safety_compliance": 0.94,
            "ethical_alignment": 0.86,
            "timestamp": time.time()
        }
        
        monitor.record_metrics(normal_metrics)
        monitor.record_metrics(anomaly_metrics)
        
        # Sprawdzanie anomalii
        anomalies = monitor.check_for_anomalies()
        
        # Powinna być wykryta jedna anomalia
        assert len(anomalies) > 0
        assert "response_quality" in anomalies[0]["metric"]


def test_handle_alert(monitor_config):
    """Test obsługi alertów."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"), \
         patch("src.modules.security.development_monitor_manager.logger") as mock_logger:
        
        monitor = DevelopmentMonitorManager(monitor_config)
        
        # Testowy alert
        alert = {
            "metric": "response_quality",
            "change": -0.3,
            "previous_value": 0.9,
            "current_value": 0.6,
            "timestamp": time.time(),
            "severity": "high"
        }
        
        # Obsługa alertu
        monitor.handle_alert(alert)
        
        # Sprawdzanie, czy alert został zapisany
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0] == alert
        
        # Sprawdzanie, czy alert został zalogowany
        mock_logger.warning.assert_called_once()


def test_generate_dashboard_data(monitor_config):
    """Test generowania danych do dashboardu."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"):
        monitor = DevelopmentMonitorManager(monitor_config)
        
        # Dodanie przykładowych metryk
        for i in range(10):
            metrics = {
                "response_quality": 0.8 + (i * 0.01),
                "metawareness_depth": 0.7 + (i * 0.02),
                "safety_compliance": 0.95 - (i * 0.005),
                "ethical_alignment": 0.85 + (i * 0.01),
                "timestamp": time.time() - (3600 - i * 360)
            }
            monitor.record_metrics(metrics)
        
        # Dodanie alertu
        monitor.handle_alert({
            "metric": "safety_compliance",
            "change": -0.05,
            "previous_value": 0.95,
            "current_value": 0.9,
            "timestamp": time.time(),
            "severity": "medium"
        })
        
        # Generowanie danych do dashboardu
        dashboard_data = monitor.generate_dashboard_data()
        
        # Sprawdzanie struktury danych dashboardu
        assert isinstance(dashboard_data, dict)
        assert "metrics_history" in dashboard_data
        assert "recent_alerts" in dashboard_data
        assert "trends" in dashboard_data
        assert len(dashboard_data["metrics_history"]) == 10
        assert len(dashboard_data["recent_alerts"]) == 1


def test_save_and_load_monitoring_data(monitor_config):
    """Test zapisywania i wczytywania danych monitoringu."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"), \
         patch("src.modules.security.development_monitor_manager.open", mock_open(), create=True), \
         patch("src.modules.security.development_monitor_manager.json.dump") as mock_json_dump, \
         patch("src.modules.security.development_monitor_manager.json.load") as mock_json_load, \
         patch("src.modules.security.development_monitor_manager.os.path.exists", return_value=True):
        
        # Przykładowe dane
        test_metrics = {
            "response_quality": 0.85,
            "metawareness_depth": 0.72,
            "safety_compliance": 0.95,
            "ethical_alignment": 0.88,
            "timestamp": time.time()
        }
        
        # Mockowanie odpowiedzi json.load
        mock_json_load.return_value = {"records": [test_metrics], "alerts": []}
        
        # Tworzenie monitora z patchowaniem load_monitoring_data
        with patch("src.modules.security.development_monitor_manager.DevelopmentMonitorManager.load_monitoring_data"):
            monitor = DevelopmentMonitorManager(monitor_config)
            
            # Resetowanie danych monitoringu
            monitor.monitoring_records = []
            monitor.alerts = []
            
            # Dodajemy przykładowe dane
            monitor.record_metrics(test_metrics)
        
        # Zapisz dane
        monitor.save_monitoring_data()
        
        # Sprawdź, czy json.dump został wywołany
        mock_json_dump.assert_called_once()
        
        # Czyszczenie danych przed wczytaniem
        monitor.monitoring_records = []
        
        # Wczytaj dane
        monitor.load_monitoring_data()
        
        # Sprawdź, czy dane zostały wczytane
        assert len(monitor.monitoring_records) == 1
        assert monitor.monitoring_records[0] == test_metrics


def test_run_monitoring_cycle(monitor_config, mock_model_manager, mock_metawareness_manager):
    """Test przeprowadzania pełnego cyklu monitorowania."""
    with patch("src.modules.security.development_monitor_manager.os.makedirs"), \
         patch("src.modules.security.development_monitor_manager.DevelopmentMonitorManager.save_monitoring_data"), \
         patch("src.modules.security.development_monitor_manager.open", mock_open(), create=True), \
         patch("src.modules.security.development_monitor_manager.json.dump"), \
         patch("src.modules.security.development_monitor_manager.logger"):
        
        # Tworzenie monitora z patchowaniem load_monitoring_data
        with patch("src.modules.security.development_monitor_manager.DevelopmentMonitorManager.load_monitoring_data"):
            monitor = DevelopmentMonitorManager(monitor_config)
            
            # Resetowanie danych monitoringu
            monitor.monitoring_records = []
            monitor.alerts = []
        
        # Przeprowadzenie cyklu monitorowania
        # Symulacja zebrania metryk
        with patch.object(monitor, 'collect_metrics') as mock_collect:
            mock_collect.return_value = {
                "response_quality": 0.85,
                "metawareness_depth": 0.72,
                "safety_compliance": 0.95,
                "ethical_alignment": 0.88,
                "timestamp": time.time()
            }
            
            monitor.run_monitoring_cycle(mock_model_manager, mock_metawareness_manager)
        
        # Sprawdzanie, czy metryki zostały zebrane i zapisane
        assert len(monitor.monitoring_records) == 1
        
        # Symulacja anomalii w następnym cyklu
        with patch.object(monitor, 'collect_metrics') as mock_collect:
            mock_collect.return_value = {
                "response_quality": 0.6,  # niższa jakość odpowiedzi
                "metawareness_depth": 0.72,
                "safety_compliance": 0.85,  # niższa zgodność z bezpieczeństwem
                "ethical_alignment": 0.88,
                "timestamp": time.time()
            }
            
            # Przeprowadzenie kolejnego cyklu z anomalią
            monitor.run_monitoring_cycle(mock_model_manager, mock_metawareness_manager)
            
            # Sprawdzanie, czy alert został wygenerowany
            assert len(monitor.alerts) > 0