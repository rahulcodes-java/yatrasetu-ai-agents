# Weather Service Integration

This is a lightweight external weather service that exposes weather information for key tourist destinations in India.

## Architecture
- **Flask Server**: Runs on `http://localhost:5001`.
- **Database**: Hardcoded curated weather data in `weather_service.py` mapping months to seasons and returning tailored advice (indoor vs outdoor activities, best time of day to sightsee, packing, monsoons, and heat warning).
- **Log file**: Saves all queries to `logs/weather_queries.log` relative to the directory it is run in.

## How to Run
From the root of the project:
```bash
python planner_mcp_weather/server.py
```

## Example API Call
```bash
curl "http://localhost:5001/weather?destination=Jaipur&month=June"
```

## Example Response
```json
{
  "best_months_to_visit": "October to March (Winter)",
  "best_visiting_season": "October to March (Winter)",
  "destination": "Jaipur",
  "key_travel_notes": "June is extremely hot. Avoid outdoor sightseeing in the afternoon (12 PM - 4 PM). Schedule visits for early mornings (before 10 AM) or late evenings. Focus on indoor air-conditioned activities (like Albert Hall Museum or shopping inside malls) during peak heat hours.",
  "monsoon_season": "July to September",
  "packing_recommendations": "Light-colored loose cotton clothes, wide-brim hat, sunglasses, high SPF sunscreen, and hydration packets/water bottles.",
  "packing_suggestions": "Light-colored loose cotton clothes, wide-brim hat, sunglasses, high SPF sunscreen, and hydration packets/water bottles.",
  "queried_month": "June",
  "season_context": "Summer",
  "status": "success",
  "temperature_range": "25°C - 45°C",
  "travel_advice": "June is extremely hot. Avoid outdoor sightseeing in the afternoon (12 PM - 4 PM). Schedule visits for early mornings (before 10 AM) or late evenings. Focus on indoor air-conditioned activities (like Albert Hall Museum or shopping inside malls) during peak heat hours.",
  "typical_temp_range": "25°C - 45°C",
  "weather_conditions": "Extremely hot, dry, and sunny. Heatwaves are common, especially in May and June."
}
```
