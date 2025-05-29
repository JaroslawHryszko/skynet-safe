"""Moduł monitorowania rozwoju systemu."""

import logging
import json
import time
import os
import statistics
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SKYNET-SAFE.DevelopmentMonitorManager")


class DevelopmentMonitorManager:
    """Klasa zarządzająca monitorowaniem rozwoju systemu."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja menedżera monitorowania.
        
        Args:
            config: Konfiguracja menedżera monitorowania zawierająca parametry takie jak
                   monitoring_interval, monitoring_metrics, alert_thresholds, itp.
        """
        self.config = config
        self.monitoring_interval = config.get("monitoring_interval", 60)  # sekundy
        self.record_history_length = config.get("record_history_length", 100)
        self.metrics = config.get("monitoring_metrics", [])
        self.alert_thresholds = config.get("alert_thresholds", {})
        self.monitoring_log_file = config.get("monitoring_log_file", "./data/security/monitoring_log.json")
        self.alert_log_file = config.get("alert_log_file", "./data/security/alerts.json")
        self.dashboard_update_interval = config.get("dashboard_update_interval", 300)  # sekundy
        
        # Inicjalizacja struktur danych
        self.monitoring_records = []
        self.alerts = []
        self.last_monitoring_time = 0
        self.last_dashboard_update = 0
        
        # Utworzenie katalogów do zapisywania danych monitorowania, jeśli nie istnieją
        os.makedirs(os.path.dirname(self.monitoring_log_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.alert_log_file), exist_ok=True)
        
        # Wczytaj istniejące dane monitorowania, jeśli dostępne
        self.load_monitoring_data()
        
        logger.info("Menedżer monitorowania rozwoju zainicjalizowany")

    def collect_metrics(self, model_manager: Any, metawareness_manager: Any) -> Dict[str, float]:
        """Zbiera metryki systemu.
        
        Args:
            model_manager: Menedżer modelu
            metawareness_manager: Menedżer metaświadomości
            
        Returns:
            Dict: Zebrane metryki
        """
        metrics = {}
        current_time = time.time()
        
        # Dodanie znacznika czasu
        metrics["timestamp"] = current_time
        
        # Zbieranie metryk na podstawie dostępnych metryk z konfiguracji
        for metric_name in self.metrics:
            # W prawdziwej implementacji wartości byłyby pobierane dynamicznie
            # Tutaj używamy przykładowych wartości dla demonstracji
            if metric_name == "response_quality":
                # Przykładowe pobranie jakości odpowiedzi z modelu
                metrics[metric_name] = getattr(model_manager, "response_quality_score", 0.85)
            elif metric_name == "metawareness_depth":
                # Przykładowe pobranie głębokości metaświadomości
                metacognitive_knowledge = metawareness_manager.get_metacognitive_knowledge()
                num_reflections = len(metacognitive_knowledge.get("reflections", []))
                num_insights = len(metacognitive_knowledge.get("insights_from_discoveries", []))
                metrics[metric_name] = min(1.0, (num_reflections + num_insights) / 10.0)
            elif metric_name == "safety_compliance":
                # Przykładowa wartość zgodności z bezpieczeństwem
                metrics[metric_name] = 0.95
            elif metric_name == "ethical_alignment":
                # Przykładowa wartość zgodności etycznej
                metrics[metric_name] = 0.88
            else:
                # Domyślna wartość dla nieznanych metryk
                metrics[metric_name] = 0.5
        
        logger.debug(f"Zebrano metryki monitorowania: {metrics}")
        return metrics

    def record_metrics(self, metrics: Dict[str, float]) -> None:
        """Zapisuje metryki w historii monitorowania.
        
        Args:
            metrics: Metryki do zapisania
        """
        # Dodaj metryki do historii
        self.monitoring_records.append(metrics)
        
        # Ogranicz długość historii
        if len(self.monitoring_records) > self.record_history_length:
            self.monitoring_records = self.monitoring_records[-self.record_history_length:]
        
        logger.debug(f"Zapisano metryki w historii monitorowania")

    def analyze_trends(self) -> Dict[str, Any]:
        """Analizuje trendy w metrykach.
        
        Returns:
            Dict: Analiza trendów dla każdej metryki
        """
        try:
            trends = {}
            
            # Jeśli brak wystarczającej liczby danych, zwróć pusty słownik
            if len(self.monitoring_records) < 2:
                logger.debug("Insufficient monitoring records for trend analysis")
                return trends
            
            # Sortuj rekordy według czasu
            try:
                sorted_records = sorted(self.monitoring_records, key=lambda x: x.get("timestamp", 0))
            except Exception as e:
                logger.error(f"Error sorting monitoring records: {e}")
                return trends
            
            # Analizuj trendy dla każdej metryki
            for metric_name in self.metrics:
                try:
                    # Zbierz wartości metryki z historii
                    values = []
                    for record in sorted_records:
                        if metric_name in record:
                            try:
                                value = float(record[metric_name])
                                values.append(value)
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Invalid metric value for {metric_name}: {record[metric_name]}")
                                continue
                    
                    if len(values) < 2:
                        logger.debug(f"Insufficient values for metric {metric_name}")
                        continue
                    
                    # Oblicz zmianę między pierwszą a ostatnią wartością
                    first_value = values[0]
                    last_value = values[-1]
                    change = last_value - first_value
                    
                    # Oblicz nachylenie linii trendu (prosta metoda)
                    if len(values) > 0:
                        avg_change = change / len(values)
                    else:
                        avg_change = 0
                    
                    # Określ kierunek trendu
                    if avg_change > 0.05:
                        trend_direction = "increasing"
                    elif avg_change < -0.05:
                        trend_direction = "decreasing"
                    else:
                        trend_direction = "stable"
                    
                    # Zapisz wyniki analizy
                    trends[f"{metric_name}_trend"] = {
                        "direction": trend_direction,
                        "average_change": avg_change,
                        "total_change": change,
                        "current_value": last_value,
                        "data_points": len(values)
                    }
                    
                    logger.debug(f"Trend analysis for {metric_name}: {trend_direction}")
                    
                except Exception as e:
                    logger.error(f"Error analyzing trend for metric {metric_name}: {e}")
                    continue
            
            logger.info(f"Completed trend analysis for {len(trends)} metrics")
            return trends
            
        except Exception as e:
            logger.error(f"Unexpected error during trend analysis: {e}")
            logger.debug("Trend analysis error details", exc_info=True)
            return {}

    def check_for_anomalies(self) -> List[Dict[str, Any]]:
        """Sprawdza anomalie w zachowaniu systemu.
        
        Returns:
            List: Lista wykrytych anomalii
        """
        try:
            anomalies = []
            
            # Brak wystarczającej liczby danych
            if len(self.monitoring_records) < 2:
                logger.debug("Insufficient monitoring records for anomaly detection")
                return anomalies
            
            # Sortuj rekordy według czasu
            try:
                sorted_records = sorted(self.monitoring_records, key=lambda x: x.get("timestamp", 0))
            except Exception as e:
                logger.error(f"Error sorting records for anomaly detection: {e}")
                return anomalies
            
            # Podziel na poprzednie i bieżące wartości
            previous_records = sorted_records[:-1]
            current_record = sorted_records[-1]
            
            if not current_record:
                logger.warning("No current record available for anomaly detection")
                return anomalies
            
            # Sprawdź anomalie dla każdej metryki
            for metric_name in self.metrics:
                try:
                    # Pobierz poprzednie wartości metryki
                    prev_values = []
                    for record in previous_records:
                        if metric_name in record:
                            try:
                                value = float(record[metric_name])
                                prev_values.append(value)
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid previous value for {metric_name}: {record[metric_name]}")
                                continue
                    
                    if not prev_values:
                        logger.debug(f"No previous values available for metric {metric_name}")
                        continue
                    
                    # Oblicz średnią i odchylenie standardowe
                    try:
                        mean_value = statistics.mean(prev_values)
                        if len(prev_values) > 1:
                            stdev_value = statistics.stdev(prev_values)
                        else:
                            stdev_value = 0
                    except statistics.StatisticsError as e:
                        logger.warning(f"Statistics error for metric {metric_name}: {e}")
                        continue
                    
                    # Pobierz bieżącą wartość
                    if metric_name not in current_record:
                        logger.debug(f"Current record missing metric {metric_name}")
                        continue
                        
                    try:
                        current_value = float(current_record[metric_name])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid current value for {metric_name}: {current_record[metric_name]}")
                        continue
                    
                    # Sprawdź, czy bieżąca wartość znacząco odbiega od poprzednich
                    if stdev_value > 0:
                        # Ile odchyleń standardowych od średniej
                        z_score = abs(current_value - mean_value) / stdev_value
                        
                        # Jeśli odchylenie jest duże (> 2 odchylenia standardowe)
                        if z_score > 2:
                            anomaly = {
                                "metric": metric_name,
                                "current_value": current_value,
                                "mean_value": mean_value,
                                "z_score": z_score,
                                "timestamp": current_record.get("timestamp", time.time()),
                                "type": "statistical_anomaly"
                            }
                            anomalies.append(anomaly)
                            continue
                            
                    # Sprawdź, czy nastąpił nagły spadek wartości
                    threshold_key = f"{metric_name}_drop"
                    if threshold_key in self.alert_thresholds:
                        drop_threshold = self.alert_thresholds[threshold_key]
                        
                        # Pobierz poprzednią wartość
                        if previous_records:
                            prev_value = previous_records[-1].get(metric_name, 0)
                            change = current_value - prev_value
                            
                            # Jeśli spadek jest większy niż próg
                            if change < -drop_threshold:
                                anomaly = {
                                    "metric": metric_name,
                                    "previous_value": prev_value,
                                    "current_value": current_value,
                                    "change": change,
                                    "threshold": drop_threshold,
                                    "timestamp": current_record.get("timestamp", time.time()),
                                    "type": "sudden_drop"
                                }
                                anomalies.append(anomaly)
                                
                except Exception as e:
                    logger.error(f"Error processing metric {metric_name}: {e}")
                    continue
        
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return []

    def handle_alert(self, alert: Dict[str, Any]) -> None:
        """Obsługuje alertu z monitorowania.
        
        Args:
            alert: Alert do obsługi
        """
        # Dodanie alertu do historii
        self.alerts.append(alert)
        
        # Ograniczenie długości historii alertów
        if len(self.alerts) > 100:  # Przechowujemy maksymalnie 100 ostatnich alertów
            self.alerts = self.alerts[-100:]
        
        # Logowanie alertu
        severity = alert.get("severity", "medium")
        if severity == "high":
            logger.warning(f"ALERT WYSOKIEGO PRIORYTETU: {alert}")
        else:
            logger.info(f"Alert: {alert}")
        
        # W rzeczywistej implementacji można tu dodać powiadomienia, e-maile, itp.

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generuje dane do dashboardu.
        
        Returns:
            Dict: Dane do dashboardu
        """
        dashboard_data = {
            "metrics_history": self.monitoring_records[-20:],  # Ostatnie 20 pomiarów
            "recent_alerts": self.alerts[-5:],  # Ostatnie 5 alertów
            "trends": self.analyze_trends(),
            "anomalies": self.check_for_anomalies(),
            "generated_at": time.time()
        }
        
        self.last_dashboard_update = time.time()
        
        return dashboard_data

    def save_monitoring_data(self) -> None:
        """Zapisuje dane monitorowania do pliku."""
        try:
            with open(self.monitoring_log_file, 'w') as f:
                json.dump({
                    "records": self.monitoring_records,
                    "alerts": self.alerts,
                    "last_monitoring_time": self.last_monitoring_time,
                    "last_dashboard_update": self.last_dashboard_update
                }, f, indent=2)
            logger.debug(f"Zapisano dane monitorowania do {self.monitoring_log_file}")
        except Exception as e:
            logger.error(f"Błąd przy zapisywaniu danych monitorowania: {e}")

    def load_monitoring_data(self) -> None:
        """Wczytuje dane monitorowania z pliku."""
        if os.path.exists(self.monitoring_log_file):
            try:
                with open(self.monitoring_log_file, 'r') as f:
                    data = json.load(f)
                    self.monitoring_records = data.get("records", [])
                    self.alerts = data.get("alerts", [])
                    self.last_monitoring_time = data.get("last_monitoring_time", 0)
                    self.last_dashboard_update = data.get("last_dashboard_update", 0)
                logger.info(f"Wczytano dane monitorowania z {self.monitoring_log_file}")
            except Exception as e:
                logger.error(f"Błąd przy wczytywaniu danych monitorowania: {e}")

    def run_monitoring_cycle(self, model_manager: Any, metawareness_manager: Any) -> None:
        """Przeprowadza pełny cykl monitorowania.
        
        Args:
            model_manager: Menedżer modelu
            metawareness_manager: Menedżer metaświadomości
        """
        current_time = time.time()
        
        # Zbieranie metryk
        metrics = self.collect_metrics(model_manager, metawareness_manager)
        
        # Zapisanie metryk
        self.record_metrics(metrics)
        
        # Sprawdzenie anomalii
        anomalies = self.check_for_anomalies()
        
        # Obsługa alertów dla wykrytych anomalii
        for anomaly in anomalies:
            alert = {
                "type": "anomaly_detected",
                "anomaly": anomaly,
                "timestamp": current_time,
                "severity": "high" if anomaly.get("type") == "sudden_drop" else "medium"
            }
            self.handle_alert(alert)
        
        # Aktualizacja czasu ostatniego monitorowania
        self.last_monitoring_time = current_time
        
        # Zapisanie danych monitorowania
        self.save_monitoring_data()
        
        # Aktualizacja dashboardu, jeśli minął odpowiedni czas
        if current_time - self.last_dashboard_update >= self.dashboard_update_interval:
            self.generate_dashboard_data()
        
        logger.info(f"Zakończono cykl monitorowania, wykryto {len(anomalies)} anomalii")

    def should_run_monitoring(self) -> bool:
        """Sprawdza, czy należy przeprowadzić cykl monitorowania.
        
        Returns:
            Bool: Czy należy przeprowadzić monitorowanie
        """
        current_time = time.time()
        
        # Sprawdź, czy minął wystarczający czas od ostatniego monitorowania
        if current_time - self.last_monitoring_time >= self.monitoring_interval:
            return True
        
        return False