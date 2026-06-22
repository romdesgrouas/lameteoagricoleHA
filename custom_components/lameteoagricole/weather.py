"""Weather platform for La Meteo Agricole."""

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN

CONDITION_MAP = {
    "orage": "lightning-rainy",
    "pluie": "rainy",
    "averse": "rainy",
    "ciel clair": "sunny",
    "ensoleill": "sunny",
    "ensoleille": "sunny",
    "soleil": "sunny",
    "peu nuageux": "partlycloudy",
    "partiellement nuageux": "partlycloudy",
    "nuageux": "cloudy",
    "couvert": "cloudy",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up La Meteo Agricole weather entity."""
    coordinator: DataUpdateCoordinator = entry.runtime_data
    async_add_entities([LaMeteoAgricoleWeather(coordinator, entry)])


class LaMeteoAgricoleWeather(CoordinatorEntity, WeatherEntity):
    """Representation of La Meteo Agricole weather."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._attr_unique_id = entry.unique_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
            "manufacturer": "lameteoagricole.net",
            "name": entry.title,
        }
        self._attr_attribution = "Data provided by lameteoagricole.net"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
        self.hass.async_create_task(self.async_update_listeners())

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        current = self.coordinator.data.current
        return _map_condition(current.condition) if current else None

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature.

        The public page exposes daily values, so this uses today's maximum.
        """
        current = self.coordinator.data.current
        return current.temperature if current else None

    @property
    def native_templow(self) -> float | None:
        """Return the current low temperature."""
        current = self.coordinator.data.current
        return getattr(current, "templow", None) if current else None

    @property
    def native_apparent_temperature(self) -> float | None:
        """Return the apparent temperature."""
        current = self.coordinator.data.current
        return getattr(current, "apparent_temperature", None) if current else None

    @property
    def humidity(self) -> int | None:
        """Return the humidity."""
        current = self.coordinator.data.current
        return getattr(current, "humidity", None) if current else None

    @property
    def cloud_coverage(self) -> int | None:
        """Return the cloud coverage."""
        current = self.coordinator.data.current
        return getattr(current, "cloud_coverage", None) if current else None

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        current = self.coordinator.data.current
        return current.wind_speed if current else None

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Return the wind gust speed."""
        current = self.coordinator.data.current
        return current.wind_gust_speed if current else None

    @property
    def wind_bearing(self) -> str | None:
        """Return wind bearing."""
        current = self.coordinator.data.current
        return current.wind_bearing if current else None

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        forecasts: list[Forecast] = []
        for day in self.coordinator.data.forecast:
            item: Forecast = {
                "datetime": day.date.isoformat(),
                "condition": _map_condition(day.condition),
                "native_temperature": day.temperature,
                "native_templow": day.templow,
                "native_precipitation": day.precipitation,
                "precipitation_probability": day.precipitation_probability,
                "native_wind_speed": day.wind_speed,
                "native_wind_gust_speed": day.wind_gust_speed,
                "wind_bearing": day.wind_bearing,
            }
            forecasts.append({key: value for key, value in item.items() if value is not None})
        return forecasts

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast."""
        forecasts: list[Forecast] = []
        for hour in self.coordinator.data.hourly_forecast:
            item: Forecast = {
                "datetime": hour.datetime.isoformat(),
                "condition": _map_condition(hour.condition),
                "native_temperature": hour.temperature,
                "native_apparent_temperature": hour.apparent_temperature,
                "native_precipitation": hour.precipitation,
                "precipitation_probability": hour.precipitation_probability,
                "native_wind_speed": hour.wind_speed,
                "native_wind_gust_speed": hour.wind_gust_speed,
                "wind_bearing": hour.wind_bearing,
                "humidity": hour.humidity,
                "cloud_coverage": hour.cloud_coverage,
            }
            forecasts.append({key: value for key, value in item.items() if value is not None})
        return forecasts


def _map_condition(label: str | None) -> str | None:
    """Map La Meteo Agricole condition labels to Home Assistant conditions."""
    if not label:
        return None
    normalized = (
        label.lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ç", "c")
    )
    for needle, condition in CONDITION_MAP.items():
        if needle in normalized:
            return condition
    return "partlycloudy"
