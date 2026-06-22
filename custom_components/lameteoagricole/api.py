"""Client and parser for lameteoagricole.net."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
import html
import json
import re
from urllib.parse import urljoin, urlparse

from aiohttp import ClientError, ClientSession

from .const import BASE_URL, USER_AGENT


class LaMeteoAgricoleError(Exception):
    """Raised when data cannot be fetched or parsed."""


@dataclass(slots=True)
class ForecastDay:
    """Daily forecast data."""

    date: date
    condition: str | None = None
    temperature: float | None = None
    templow: float | None = None
    precipitation: float | None = None
    precipitation_probability: int | None = None
    wind_bearing: str | None = None
    wind_speed: float | None = None
    wind_gust_speed: float | None = None
    apparent_temperature: float | None = None
    humidity: int | None = None
    cloud_coverage: int | None = None


@dataclass(slots=True)
class ForecastHour:
    """Hourly forecast data."""

    datetime: datetime
    condition: str | None = None
    temperature: float | None = None
    precipitation: float | None = None
    precipitation_probability: int | None = None
    wind_bearing: str | None = None
    wind_speed: float | None = None
    wind_gust_speed: float | None = None
    apparent_temperature: float | None = None
    humidity: int | None = None
    cloud_coverage: int | None = None


@dataclass(slots=True)
class WeatherData:
    """Weather data returned by the site."""

    location_name: str | None
    forecast: list[ForecastDay]
    hourly_forecast: list[ForecastHour]

    @property
    def current(self) -> ForecastHour | ForecastDay | None:
        """Return the nearest hourly forecast, then today's daily forecast."""
        if self.hourly_forecast:
            return self.hourly_forecast[0]
        return self.forecast[0] if self.forecast else None


class LaMeteoAgricoleClient:
    """Small async client for La Meteo Agricole."""

    def __init__(self, session: ClientSession, url: str) -> None:
        """Initialize the client."""
        self._session = session
        self._url = normalize_url(url)

    async def async_get_weather(self) -> WeatherData:
        """Fetch and parse weather data."""
        text = await self._async_fetch_text(self._url)

        try:
            weather = parse_weather_page(text)
        except (IndexError, ValueError, AttributeError, TypeError) as err:
            raise LaMeteoAgricoleError("Cannot parse La Meteo Agricole page") from err

        hourly_url = _extract_hourly_url(text, self._url) or _to_hourly_url(self._url)
        if hourly_url:
            try:
                hourly_text = await self._async_fetch_text(hourly_url)
                weather.hourly_forecast = parse_hourly_page(hourly_text)
            except LaMeteoAgricoleError:
                raise
            except (IndexError, ValueError, AttributeError, TypeError) as err:
                raise LaMeteoAgricoleError("Cannot parse hourly La Meteo Agricole page") from err

        return weather

    async def _async_fetch_text(self, url: str) -> str:
        """Fetch a page."""
        try:
            async with self._session.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            ) as response:
                response.raise_for_status()
                return await response.text()
        except (ClientError, TimeoutError) as err:
            raise LaMeteoAgricoleError(f"Cannot fetch {url}: {err}") from err


def normalize_url(value: str) -> str:
    """Normalize either a full URL or a communehome code."""
    value = value.strip()
    if value.isdigit():
        return BASE_URL.format(commune=value)

    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return value

    raise LaMeteoAgricoleError("Enter a full URL or a communehome numeric code")


def parse_weather_page(markup: str) -> WeatherData:
    """Parse a La Meteo Agricole public forecast page."""
    location_name = _parse_location_name(markup)
    base_year = _parse_valid_from(markup).year

    table = _extract_table(markup)
    headers = _extract_headers(table, base_year)
    cells = _extract_body_cells(table)

    forecasts = [
        _parse_forecast_cell(day, cell)
        for day, cell in zip(headers, cells, strict=False)
    ]
    forecasts = [forecast for forecast in forecasts if forecast.condition or forecast.temperature]

    if not forecasts:
        raise ValueError("No forecast values found")

    return WeatherData(location_name=location_name, forecast=forecasts, hourly_forecast=[])


def parse_hourly_page(markup: str) -> list[ForecastHour]:
    """Parse a La Meteo Agricole hourly forecast page."""
    base_date = _parse_valid_from(markup)
    table = _extract_table(markup, "heures-table")
    headers = _extract_hourly_headers(table, base_date)
    cells = _extract_body_cells(table)

    forecasts = [
        _parse_hourly_cell(moment, cell)
        for moment, cell in zip(headers, cells, strict=False)
    ]
    forecasts = [forecast for forecast in forecasts if forecast.condition or forecast.temperature]
    if not forecasts:
        raise ValueError("No hourly forecast values found")
    return forecasts


def _parse_location_name(markup: str) -> str | None:
    """Extract location name from schema.org JSON-LD when available."""
    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        markup,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        try:
            data = json.loads(html.unescape(block))
        except json.JSONDecodeError:
            continue
        if data.get("@type") != "WeatherForecast":
            continue
        place = data.get("spatialCoverage") or {}
        name = place.get("name")
        address = place.get("address") or {}
        postal_code = address.get("postalCode")
        if name and postal_code:
            return f"{name} ({postal_code})"
        if name:
            return str(name)
    return None


def _parse_valid_from(markup: str) -> date:
    """Extract the forecast start date from JSON-LD."""
    match = re.search(r'"validFrom"\s*:\s*"(\d{4}-\d{2}-\d{2})"', markup)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    return date.today()


def _extract_table(markup: str, table_id: str = "jours-table") -> str:
    """Extract a forecast table."""
    match = re.search(
        rf'<table[^>]+id=["\']{re.escape(table_id)}["\'][^>]*>(.*?)</table>',
        markup,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        raise ValueError("Forecast table not found")
    return match.group(1)


def _extract_hourly_headers(table: str, base_date: date) -> list[datetime]:
    """Extract forecast datetimes from hourly table header cells."""
    thead = re.search(r"<thead[^>]*>(.*?)</thead>", table, flags=re.IGNORECASE | re.DOTALL)
    if not thead:
        raise ValueError("Hourly forecast header not found")

    year = base_date.year
    month = base_date.month
    previous_day = 0
    moments: list[datetime] = []

    for th in re.findall(r"<th[^>]*>(.*?)</th>", thead.group(1), flags=re.IGNORECASE | re.DOTALL):
        parts = [_clean_text(part) for part in re.findall(r"<span[^>]*>(.*?)</span>", th, flags=re.DOTALL)]
        day = next((int(part) for part in parts if part and part.isdigit()), None)
        hour_label = next((part for part in parts if part and re.fullmatch(r"\d{1,2}h", part)), None)
        if day is None or hour_label is None:
            continue

        if previous_day and day < previous_day:
            month += 1
            if month > 12:
                month = 1
                year += 1
        previous_day = day
        hour = int(hour_label.removesuffix("h"))
        moments.append(datetime.combine(date(year, month, day), time(hour=hour)))

    return moments


def _extract_headers(table: str, base_year: int) -> list[date]:
    """Extract forecast dates from table header cells."""
    thead = re.search(r"<thead[^>]*>(.*?)</thead>", table, flags=re.IGNORECASE | re.DOTALL)
    if not thead:
        raise ValueError("Forecast header not found")

    year = base_year
    previous_month = 0
    days: list[date] = []

    for th in re.findall(r"<th[^>]*>(.*?)</th>", thead.group(1), flags=re.IGNORECASE | re.DOTALL):
        parts = [_clean_text(part) for part in re.findall(r"<span[^>]*>(.*?)</span>", th, flags=re.DOTALL)]
        day = next((int(part) for part in parts if part.isdigit()), None)
        month_label = next((part for part in parts if _month_number(part)), None)
        if day is None or month_label is None:
            continue

        month = _month_number(month_label)
        if previous_month and month < previous_month:
            year += 1
        previous_month = month
        days.append(date(year, month, day))

    return days


def _extract_body_cells(table: str) -> list[str]:
    """Extract body forecast cells."""
    tbody = re.search(r"<tbody[^>]*>(.*?)</tbody>", table, flags=re.IGNORECASE | re.DOTALL)
    if not tbody:
        raise ValueError("Forecast body not found")
    return re.findall(r"<td[^>]*>(.*?)</td>", tbody.group(1), flags=re.IGNORECASE | re.DOTALL)


def _parse_forecast_cell(day: date, cell: str) -> ForecastDay:
    """Parse one forecast day cell."""
    condition = _first_match(cell, r'Weather/numbers/\d+\.svg"[^>]+alt="([^"]+)"')
    temperature = _number(_first_match(cell, r'fw-bold fs-4[^>]*>\s*(-?\d+)'))
    templow = _number(_first_match(cell, r"min(?:&nbsp;|\s)*(-?\d+)"))

    precipitation_text = _first_match(
        cell,
        r"Pr[^<]+cipitations\s*:</span>\s*<span[^>]*>(.*?)</span>",
    )
    precipitation = _precipitation_amount(precipitation_text)

    probability = _integer(_first_match(cell, r"Probabilit[^:]+:\s*(\d+)%"))
    wind_bearing = _first_match(cell, r"Direction du vent\s*:\s*([^\"<]+)")
    wind_speed = _number(_first_match(cell, r'fw-bold">(\d+)</span><span[^>]*>km/h</span>'))
    gust_candidates = re.findall(r"(\d+)\s*km/h", _clean_text(cell))
    wind_gust_speed = _number(gust_candidates[-1]) if len(gust_candidates) > 1 else None

    return ForecastDay(
        date=day,
        condition=_clean_text(condition),
        temperature=temperature,
        templow=templow,
        precipitation=precipitation,
        precipitation_probability=probability,
        wind_bearing=_clean_text(wind_bearing),
        wind_speed=wind_speed,
        wind_gust_speed=wind_gust_speed,
    )


def _parse_hourly_cell(moment: datetime, cell: str) -> ForecastHour:
    """Parse one hourly forecast cell."""
    condition = _first_match(cell, r'Weather/numbers/\d+\.svg"[^>]+alt="([^"]+)"')
    temperature = _number(_first_match(cell, r'fw-bold fs-4[^>]*>\s*(-?\d+(?:[,.]\d+)?)'))
    apparent_temperature = _number(
        _first_match(cell, r"Temp[^<]*ressentie\s*(-?\d+(?:[,.]\d+)?)")
    )
    precipitation_text = _first_match(
        cell,
        r"Pr[^<]+cipitations\s*:</span>\s*<span[^>]*>(.*?)</span>",
    )
    precipitation = _precipitation_amount(precipitation_text)
    probability = _integer(_first_match(cell, r"Probabilit[^:]+:\s*(\d+)%"))
    wind_bearing = _first_match(cell, r"Direction du vent\s*:\s*([^\"<]+)")
    wind_speed = _number(_first_match(cell, r'fw-bold">(\d+)</span><span[^>]*>km/h</span>'))
    gust_candidates = re.findall(r"(\d+)\s*km/h", _clean_text(cell))
    wind_gust_speed = _number(gust_candidates[-1]) if len(gust_candidates) > 1 else None
    humidity = _integer(_metric_before_label(cell, r">\s*Humidit"))
    cloud_coverage = _integer(_metric_before_label(cell, r">\s*N.bulosit"))

    return ForecastHour(
        datetime=moment,
        condition=_clean_text(condition),
        temperature=temperature,
        precipitation=precipitation,
        precipitation_probability=probability,
        wind_bearing=_clean_text(wind_bearing),
        wind_speed=wind_speed,
        wind_gust_speed=wind_gust_speed,
        apparent_temperature=apparent_temperature,
        humidity=humidity,
        cloud_coverage=cloud_coverage,
    )


def _extract_hourly_url(markup: str, base_url: str) -> str | None:
    """Extract the hourly forecast URL from a page."""
    match = re.search(
        r'href=["\']([^"\']*/meteo-heure-par-heure/[^"\']+\.html)["\']',
        markup,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return urljoin(base_url, html.unescape(match.group(1)))


def _to_hourly_url(url: str) -> str | None:
    """Derive an hourly URL from a pretty daily forecast URL."""
    parsed = urlparse(url)
    if "/meteo-heure-par-heure/" in parsed.path:
        return url
    if "/previsions-meteo-agricole/" in parsed.path:
        return url.replace("/previsions-meteo-agricole/", "/meteo-heure-par-heure/")
    return None


def _month_number(label: str) -> int:
    """Return French month number."""
    normalized = _normalize(label)
    months = {
        "janvier": 1,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "decembre": 12,
    }
    return months.get(normalized, 0)


def _precipitation_amount(value: str | None) -> float | None:
    """Parse precipitation amount, using the upper bound for ranges."""
    if not value:
        return None
    numbers = re.findall(r"\d+(?:[,.]\d+)?", _clean_text(value))
    if not numbers:
        return None
    return float(numbers[-1].replace(",", "."))


def _first_match(value: str, pattern: str) -> str | None:
    """Return first regex capture."""
    match = re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return html.unescape(match.group(1))


def _metric_before_label(value: str, label_pattern: str) -> str | None:
    """Return the numeric metric in the block that precedes a label."""
    label = re.search(label_pattern, value, flags=re.IGNORECASE | re.DOTALL)
    if not label:
        return None
    prefix = value[max(0, label.start() - 400) : label.start()]
    matches = re.findall(
        r'<span class="fw-bold">(\d+)</span>\s*<span[^>]*>%</span>',
        prefix,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return matches[-1] if matches else None


def _number(value: str | None) -> float | None:
    """Parse a float."""
    if value is None:
        return None
    return float(value.replace(",", "."))


def _integer(value: str | None) -> int | None:
    """Parse an integer."""
    if value is None:
        return None
    return int(value)


def _clean_text(value: str | None) -> str | None:
    """Strip HTML tags and normalize spaces."""
    if value is None:
        return None
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _normalize(value: str) -> str:
    """Normalize French labels for matching."""
    return (
        value.lower()
        .strip(". ")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("û", "u")
        .replace("ù", "u")
        .replace("à", "a")
        .replace("â", "a")
        .replace("ô", "o")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ç", "c")
    )
