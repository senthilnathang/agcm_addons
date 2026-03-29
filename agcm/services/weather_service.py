"""Weather service — forecast fetching from weather.gov + manual weather CRUD.

Two weather models:
  - WeatherForecast (auto-fetched): 6 time slots (6am,9am,12pm,3pm,6pm,9pm) from weather.gov
  - Weather (manual): user-entered actual observed conditions

API routing logic (from Odoo):
  - Past dates   → weather.gov observation stations (historical actuals)
  - Today        → merge history observations + future forecast
  - Future dates → weather.gov hourly forecast
"""

import logging
from datetime import date, datetime
from typing import List, Optional

import requests
from sqlalchemy.orm import Session

from addons.agcm.models.project import Project
from addons.agcm.models.weather import Weather, WeatherForecast
from addons.agcm.services.sequence_service import next_sequence

logger = logging.getLogger(__name__)

# Weather code mapping: numeric code → label
WEATHER_CODES = {1: "Clear", 2: "Cloudy", 3: "Light Rain", 4: "Heavy Rain", 5: "Thunder"}

# Time slots fetched per day
TIME_HOURS = [6, 9, 12, 15, 18, 21]
TIME_LABELS = {6: "6 AM", 9: "9 AM", 12: "12 PM", 15: "3 PM", 18: "6 PM", 21: "9 PM"}


def _classify_weather(description: str) -> int:
    """Classify weather description text into a weather_code (1-5)."""
    words = (description or "").split()
    if "Clear" in words or "Sunny" in words:
        return 1
    elif "Cloudy" in words:
        return 2
    elif "Showers" in words:
        return 3
    elif "Rain" in words:
        return 4
    elif "Thunderstorms" in words or "Thunder" in words:
        return 5
    return 1  # default sunny


class WeatherService:
    """Handles weather forecast fetching and manual weather entry."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # =========================================================================
    # Forecast fetch (auto from weather.gov)
    # =========================================================================

    def fetch_forecast(self, project_id: int, log_date: date, dailylog_id: int) -> List[dict]:
        """
        Fetch weather forecast for a project location and date.

        Logic (matching Odoo):
        - If forecast already exists for this project+date, skip
        - Past dates: fetch from observation stations (historical)
        - Today: merge history + future forecast
        - Future: fetch hourly forecast
        """
        # Check if already fetched
        existing = (
            self.db.query(WeatherForecast)
            .filter(WeatherForecast.project_id == project_id, WeatherForecast.date == log_date)
            .count()
        )
        if existing > 0:
            return self._get_forecasts(dailylog_id)

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.project_latitude or not project.project_longitude:
            logger.warning(f"Project {project_id} has no coordinates, skipping weather fetch")
            return []

        today = date.today()
        try:
            if log_date < today:
                records = self._fetch_history(project, str(log_date), dailylog_id)
            elif log_date == today:
                records = self._fetch_present(project, str(log_date), dailylog_id)
            else:
                records = self._fetch_future(project, str(log_date), dailylog_id)
        except Exception as e:
            logger.error(f"Weather fetch failed for project {project_id}, date {log_date}: {e}")
            return []

        # Save to DB
        for rec in records:
            rec["company_id"] = self.company_id
            rec["project_id"] = project_id
            rec["dailylog_id"] = dailylog_id
            rec["date"] = log_date
            wf = WeatherForecast(**rec)
            self.db.add(wf)

        self.db.commit()
        return self._get_forecasts(dailylog_id)

    def _get_forecasts(self, dailylog_id: int) -> List[dict]:
        """Get existing forecast records for a daily log."""
        items = (
            self.db.query(WeatherForecast)
            .filter(WeatherForecast.dailylog_id == dailylog_id)
            .order_by(WeatherForecast.time_interval)
            .all()
        )
        return [
            {
                "id": f.id,
                "time_interval": f.time_interval,
                "temperature": f.temperature,
                "humidity": f.humidity,
                "wind": f.wind,
                "precipitation": f.precipitation,
                "weather_code": f.weather_code,
                "weather_label": WEATHER_CODES.get(f.weather_code, "N/A"),
            }
            for f in items
        ]

    def _weather_gov_points(self, lat, lng):
        """Call weather.gov points API to get station/forecast URLs."""
        url = f"https://api.weather.gov/points/{lat},{lng}"
        headers = {"User-Agent": "AGCM-FastVue/1.0 (construction-daily-log)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _fetch_history(self, project, log_date: str, dailylog_id: int) -> List[dict]:
        """Fetch historical observations from the nearest weather station."""
        data = self._weather_gov_points(project.project_latitude, project.project_longitude)
        stations_url = data["properties"]["observationStations"]

        headers = {"User-Agent": "AGCM-FastVue/1.0"}
        station_resp = requests.get(stations_url, headers=headers, timeout=15)
        station_resp.raise_for_status()
        station_id = station_resp.json()["features"][0]["properties"]["stationIdentifier"]

        obs_url = f"https://api.weather.gov/stations/{station_id}/observations"
        obs_resp = requests.get(obs_url, headers=headers, timeout=15)
        obs_resp.raise_for_status()
        obs_data = obs_resp.json()

        times = [f"{log_date}T{h:02d}" for h in TIME_HOURS]
        retrieved = {}
        for period in obs_data.get("features", []):
            ts = period["properties"]["timestamp"].split(":")[0]
            if ts in times:
                retrieved[ts] = period["properties"]

        records = []
        for t in times:
            if t in retrieved:
                props = retrieved[t]
                temp_c = props["temperature"]["value"]
                if temp_c is None:
                    temp_c = props.get("dewpoint", {}).get("value", 0) or 0
                temp_f = round((temp_c * 9 / 5) + 32) if temp_c else 0
                humidity = round(props.get("relativeHumidity", {}).get("value") or 0)
                wind = float(props.get("windSpeed", {}).get("value") or 0)
                description = props.get("textDescription", "")

                records.append({
                    "time_interval": t + ":00",
                    "temperature": temp_f,
                    "humidity": humidity,
                    "wind": wind,
                    "weather_code": _classify_weather(description),
                })
        return records

    def _fetch_future(self, project, log_date: str, dailylog_id: int) -> List[dict]:
        """Fetch hourly forecast for a future date."""
        data = self._weather_gov_points(project.project_latitude, project.project_longitude)
        forecast_url = data["properties"]["forecastHourly"]

        headers = {"User-Agent": "AGCM-FastVue/1.0"}
        resp = requests.get(forecast_url, headers=headers, timeout=15)
        resp.raise_for_status()
        forecast_data = resp.json()

        times = [f"{log_date}T{h:02d}" for h in TIME_HOURS]
        retrieved = {}
        for period in forecast_data.get("properties", {}).get("periods", []):
            start = period["startTime"].split(":")[0]
            if start in times:
                retrieved[start] = period

        records = []
        for t in times:
            if t in retrieved:
                p = retrieved[t]
                wind_str = str(p.get("windSpeed", "0"))
                wind_val = float("".join(c for c in wind_str if c.isdigit() or c == ".") or "0")
                precip = p.get("probabilityOfPrecipitation", {}).get("value") or 0

                records.append({
                    "time_interval": t + ":00",
                    "temperature": p["temperature"],
                    "humidity": round(p.get("relativeHumidity", {}).get("value") or 0),
                    "wind": wind_val,
                    "precipitation": float(precip),
                    "weather_code": _classify_weather(p.get("shortForecast", "")),
                })
        return records

    def _fetch_present(self, project, log_date: str, dailylog_id: int) -> List[dict]:
        """Fetch today's weather: merge history observations + future forecast."""
        history = self._fetch_history(project, log_date, dailylog_id)
        future = self._fetch_future(project, log_date, dailylog_id)

        combined = {}
        for rec in history:
            combined[rec["time_interval"]] = rec
        for rec in future:
            combined[rec["time_interval"]] = rec

        return list(combined.values())

    # =========================================================================
    # Manual weather entry CRUD
    # =========================================================================

    def list_manual_weather(self, dailylog_id: int) -> List[dict]:
        """List manual weather entries for a daily log."""
        items = (
            self.db.query(Weather)
            .filter(Weather.dailylog_id == dailylog_id)
            .order_by(Weather.id)
            .all()
        )
        return [
            {
                "id": w.id,
                "sequence_name": w.sequence_name,
                "date": str(w.date) if w.date else None,
                "temperature": w.temperature,
                "temperature_type": w.temperature_type,
                "climate_type": w.climate_type,
                "humidity": w.humidity,
                "wind": w.wind,
                "precipitation": w.precipitation,
                "rain": w.rain,
                "rain_fall": w.rain_fall,
            }
            for w in items
        ]

    def create_manual_weather(self, dailylog_id: int, data: dict) -> Weather:
        """Create a manual weather observation."""
        w = Weather(
            company_id=self.company_id,
            dailylog_id=dailylog_id,
            sequence_name=next_sequence(self.db, Weather, self.company_id),
            date=data.get("date"),
            temperature=data.get("temperature", 0),
            temperature_type=data.get("temperature_type", "F"),
            climate_type=data.get("climate_type", "clear"),
            humidity=data.get("humidity", 0),
            wind=data.get("wind", 0),
            precipitation=data.get("precipitation", 0),
            rain=data.get("rain", False),
            rain_fall=data.get("rain_fall", 0),
            project_id=data.get("project_id"),
        )
        self.db.add(w)
        self.db.commit()
        self.db.refresh(w)
        return w
