"""Weather and WeatherForecast models"""

import enum

from sqlalchemy import (
    Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Boolean, Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class ClimateType(str, enum.Enum):
    DRY = "dry"
    WET = "wet"
    CLEAR = "clear"
    CLOUDY = "cloudy"


class TemperatureUnit(str, enum.Enum):
    FAHRENHEIT = "F"
    CELSIUS = "C"


# Weather code mapping (used by forecast APIs):
# 1 = Clear, 2 = Cloudy, 3 = Light Rain, 4 = Heavy Rain, 5 = Thunder
WEATHER_CODE_MAP = {
    1: "Clear",
    2: "Cloudy",
    3: "Light Rain",
    4: "Heavy Rain",
    5: "Thunder",
}


class Weather(Base, TimestampMixin):
    """
    Manual weather entry for a daily log.

    Migrated from Odoo 'weather' model.
    Also used by the CRON-based auto-post system.
    """
    __tablename__ = "agcm_weather"
    _description = "Manual weather observations for daily logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    date = Column(Date, nullable=True)
    date_time = Column(DateTime(timezone=True), nullable=True)

    # Weather data
    temperature = Column(Float, default=0.0, nullable=True)
    temperature_type = Column(
        Enum(TemperatureUnit),
        default=TemperatureUnit.FAHRENHEIT,
        nullable=True,
    )
    climate_type = Column(
        Enum(ClimateType),
        default=ClimateType.CLEAR,
        nullable=True,
    )
    rain = Column(Boolean, default=False, nullable=True)
    rain_fall = Column(Float, default=0.0, nullable=True)
    humidity = Column(Float, default=0.0, nullable=True)
    precipitation = Column(Float, default=0.0, nullable=True)
    wind = Column(Float, default=0.0, nullable=True)
    weather_icon_src = Column(String(500), nullable=True)

    # Daily log link
    dailylog_id = Column(
        Integer,
        ForeignKey("agcm_daily_activity_logs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Project link
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Copy tracking
    copy_id = Column(
        Integer,
        ForeignKey("agcm_weather.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="weather_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_weather_dailylog", "dailylog_id"),
    )


class WeatherForecast(Base, TimestampMixin):
    """
    Auto-fetched weather forecast data.

    Populated from weather.gov (future/present) or open-meteo (historical).
    6 time slots per day: 6am, 9am, 12pm, 3pm, 6pm, 9pm.
    """
    __tablename__ = "agcm_weather_forecasts"
    _description = "Auto-fetched weather forecast data at 3-hour intervals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_name = Column(String(50), nullable=True)
    date = Column(Date, nullable=True, index=True)
    time_interval = Column(String(20), nullable=True)  # e.g. "2024-01-15T06:00"

    # Weather data
    temperature = Column(Float, default=0.0, nullable=True)
    temperature_type = Column(
        Enum(TemperatureUnit),
        default=TemperatureUnit.FAHRENHEIT,
        nullable=True,
    )
    weather_code = Column(Integer, default=0, nullable=True)  # 1-5 mapping
    humidity = Column(Float, default=0.0, nullable=True)
    wind = Column(Float, default=0.0, nullable=True)
    precipitation = Column(Float, default=0.0, nullable=True)

    # Daily log link
    dailylog_id = Column(
        Integer,
        ForeignKey("agcm_daily_activity_logs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Project link
    project_id = Column(
        Integer,
        ForeignKey("agcm_projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    dailylog = relationship("agcm_daily_activity_logs", back_populates="weather_forecast_lines", lazy="select")
    project = relationship("agcm_projects", foreign_keys=[project_id], lazy="select")

    __table_args__ = (
        Index("ix_agcm_weather_forecast_project_date", "project_id", "date"),
        Index("ix_agcm_weather_forecast_dailylog", "dailylog_id"),
    )
