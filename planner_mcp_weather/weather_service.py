# weather_service.py - Curated weather database and lookup logic

# Map months to seasonal keys
MONTH_TO_SEASON = {
    "january": "winter",
    "february": "winter",
    "march": "winter",  # Transition/spring
    "april": "summer",
    "may": "summer",
    "june": "summer",
    "july": "monsoon",
    "august": "monsoon",
    "september": "monsoon",
    "october": "winter",  # Autumn/transition
    "november": "winter",
    "december": "winter"
}

# Curated weather data for 5+ destinations
WEATHER_DATABASE = {
    "jaipur": {
        "destination": "Jaipur",
        "seasons": {
            "winter": {
                "temperature_range": "8°C - 26°C",
                "weather_conditions": "Clear blue skies, sunny days, and chilly nights. Perfect sightseeing weather.",
                "packing_suggestions": "Light woolens or jackets for evenings, comfortable cottons/linens for daytime, sunglasses.",
                "travel_advice": "Ideal for all outdoor activities including fort visits, walking tours, and open-air dining. Best time to explore Amer Fort and Hawa Mahal."
            },
            "summer": {
                "temperature_range": "25°C - 45°C",
                "weather_conditions": "Extremely hot, dry, and sunny. Heatwaves are common, especially in May and June.",
                "packing_suggestions": "Light-colored loose cotton clothes, wide-brim hat, sunglasses, high SPF sunscreen, and hydration packets/water bottles.",
                "travel_advice": "June is extremely hot. Avoid outdoor sightseeing in the afternoon (12 PM - 4 PM). Schedule visits for early mornings (before 10 AM) or late evenings. Focus on indoor air-conditioned activities (like Albert Hall Museum or shopping inside malls) during peak heat hours."
            },
            "monsoon": {
                "temperature_range": "22°C - 33°C",
                "weather_conditions": "Humid with moderate rainfall. The landscape becomes lush green.",
                "packing_suggestions": "Umbrella, light raincoat, quick-dry clothing, and sturdy waterproof footwear.",
                "travel_advice": "Forts look stunning and green, especially Nahargarh. Watch out for temporary waterlogging in old city streets. Sudden rain showers may disrupt open-air travel."
            }
        },
        "best_visiting_season": "October to March (Winter)",
        "monsoon_season": "July to September"
    },
    "goa": {
        "destination": "Goa",
        "seasons": {
            "winter": {
                "temperature_range": "20°C - 32°C",
                "weather_conditions": "Pleasant, sunny with cool sea breezes. Low humidity.",
                "packing_suggestions": "Shorts, t-shirts, swimwear, light dresses, sunglasses, flip-flops, and sunscreen.",
                "travel_advice": "Peak tourist season. All beach shacks, water sports, and night markets are fully operational. Perfect for beach activities and sunset cruises."
            },
            "summer": {
                "temperature_range": "25°C - 35°C",
                "weather_conditions": "Hot and highly humid. Afternoon heat can be draining.",
                "packing_suggestions": "Breathable cottons, linen clothing, sunglasses, sun hat, and waterproof sunscreen.",
                "travel_advice": "Enjoy early morning or late evening beach walks. Spend mid-day in air-conditioned indoor spaces or shaded pool areas. Prices are lower during this off-season."
            },
            "monsoon": {
                "temperature_range": "24°C - 30°C",
                "weather_conditions": "Heavy, continuous rainfall with high humidity. Stormy winds near beaches.",
                "packing_suggestions": "Sturdy umbrella, raincoat, waterproof bags, sandals/slippers, and quick-dry clothing.",
                "travel_advice": "Water sports and beach shacks are closed due to rough seas. However, the countryside is incredibly lush. Great time to visit Dudhsagar Waterfalls and spice plantations at lower costs."
            }
        },
        "best_visiting_season": "November to February",
        "monsoon_season": "June to October"
    },
    "delhi": {
        "destination": "Delhi",
        "seasons": {
            "winter": {
                "temperature_range": "3°C - 22°C",
                "weather_conditions": "Cold and foggy mornings, sunny pleasant afternoons. Smog/air pollution can be high in November/December.",
                "packing_suggestions": "Heavy woolens, thermals, gloves, scarf, and a warm winter coat.",
                "travel_advice": "Excellent daytime weather for heritage walks (Qutub Minar, Red Fort). Carry an N95 mask if air pollution levels (AQI) are high in early winter."
            },
            "summer": {
                "temperature_range": "28°C - 45°C",
                "weather_conditions": "Scorching heat waves (Loo winds) and dry air. Extremely intense sun.",
                "packing_suggestions": "Loose light-colored clothing, sunglasses, scarf to cover face, sun hat, and high SPF sunscreen.",
                "travel_advice": "Limit outdoor exposure during midday. Sightsee early in the morning or after sunset. Visit indoor air-conditioned places like the National Gallery of Modern Art, Akshardham exhibition halls, or indoor malls in the afternoon."
            },
            "monsoon": {
                "temperature_range": "25°C - 35°C",
                "weather_conditions": "Hot, humid, with frequent heavy rain showers. Waterlogging is common on roads.",
                "packing_suggestions": "Raincoat, umbrella, waterproof shoes, and mosquito repellent.",
                "travel_advice": "Traffic congestion can occur due to rain. Keep buffer time for transit. Check indoor options if heavy rain is forecasted."
            }
        },
        "best_visiting_season": "October to November & February to March",
        "monsoon_season": "July to September"
    },
    "varanasi": {
        "destination": "Varanasi",
        "seasons": {
            "winter": {
                "temperature_range": "5°C - 23°C",
                "weather_conditions": "Chilly, foggy mornings followed by sunny and pleasant days.",
                "packing_suggestions": "Sweaters, warm shawl/scarf, comfortable walking shoes, and thermals for early morning boat rides.",
                "travel_advice": "Perfect for attending the morning Subah-e-Banaras at Assi Ghat and evening Ganga Aarti. Fog might delay early morning boat rides, so plan accordingly."
            },
            "summer": {
                "temperature_range": "26°C - 46°C",
                "weather_conditions": "Intensely hot, dry, and dusty. Scorching heat waves (Loo) in May/June.",
                "packing_suggestions": "Light cotton clothing, sunscreen, sunglasses, scarf/hat, and ORS/hydration drinks.",
                "travel_advice": "Sightseeing should be restricted to early mornings and late evenings. Rest indoors in the afternoon. Ganga Aarti is still held, but standing in the open heat can be exhausting."
            },
            "monsoon": {
                "temperature_range": "24°C - 33°C",
                "weather_conditions": "Humid with heavy rain. The water level of the River Ganges rises significantly.",
                "packing_suggestions": "Raincoat, umbrella, shoes with excellent grip (ghat steps become very slippery).",
                "travel_advice": "Due to rising river levels during late monsoon (August-September), boat rides are often banned for safety, and access to lower ghat steps is submerged. Confirm boat availability before planning."
            }
        },
        "best_visiting_season": "October to March",
        "monsoon_season": "July to September"
    },
    "rajasthan": {
        "destination": "Rajasthan",
        "seasons": {
            "winter": {
                "temperature_range": "7°C - 28°C",
                "weather_conditions": "Sunny, crisp days and cold to near-freezing nights (especially in desert areas like Jaisalmer).",
                "packing_suggestions": "Layers of clothing - warm jackets/sweaters for nights, light cottons for daytime, sunscreen, and lip balm.",
                "travel_advice": "Best season to visit forts, lakes, and dunes. Ideal for camel safaris, desert camping, and cultural festivals."
            },
            "summer": {
                "temperature_range": "26°C - 48°C",
                "weather_conditions": "Blistering desert heat, dry winds, and extreme sun exposure.",
                "packing_suggestions": "Breathable light fabrics, sunglasses, sun hat, heavy sunscreen, and plenty of water/electrolytes.",
                "travel_advice": "Desert excursions (safaris, dune camping) are not recommended due to heat. Plan visits to cooler regions like Mount Abu, or restrict sightseeing to early mornings/late evenings."
            },
            "monsoon": {
                "temperature_range": "24°C - 35°C",
                "weather_conditions": "Humid with light to moderate rainfall. The lakes in Udaipur fill up and the Aravalli hills turn green.",
                "packing_suggestions": "Umbrella, light raincoat, waterproof footwear, and light cottons.",
                "travel_advice": "Udaipur (the Lake City) and Bundi look exceptionally beautiful. A good off-peak season to experience heritage hotels at discount prices."
            }
        },
        "best_visiting_season": "October to March",
        "monsoon_season": "July to September"
    }
}

def get_weather(destination: str, month: str = None) -> dict:
    """Looks up curated weather data for a destination, optionally filtered by month.
    
    Args:
        destination: Name of the destination/city.
        month: Name of the month (optional).
        
    Returns:
        dict: Curated weather details.
    """
    dest_key = destination.strip().lower()
    
    # Fuzzy matching for known destinations
    matched_key = None
    for k in WEATHER_DATABASE.keys():
        if k in dest_key or dest_key in k:
            matched_key = k
            break
            
    if not matched_key:
        return {
            "status": "not_found",
            "message": f"Curated weather data is only available for: {', '.join(k.capitalize() for k in WEATHER_DATABASE.keys())}."
        }
        
    data = WEATHER_DATABASE[matched_key]
    
    # Determine season based on month if provided
    season_name = "winter"  # default general display season
    selected_month = None
    
    if month:
        m_cleaned = month.strip().lower()
        if m_cleaned in MONTH_TO_SEASON:
            season_name = MONTH_TO_SEASON[m_cleaned]
            selected_month = m_cleaned.capitalize()
            
    # Extract season specific details
    season_data = data["seasons"][season_name]
    
    return {
        "status": "success",
        "destination": data["destination"],
        "queried_month": selected_month,
        "season_context": season_name.capitalize(),
        "temperature_range": season_data["temperature_range"],
        "weather_conditions": season_data["weather_conditions"],
        "best_visiting_season": data["best_visiting_season"],
        "monsoon_season": data["monsoon_season"],
        "packing_suggestions": season_data["packing_suggestions"],
        "travel_advice": season_data["travel_advice"],
        # Backwards compatibility keys
        "typical_temp_range": season_data["temperature_range"],
        "best_months_to_visit": data["best_visiting_season"],
        "packing_recommendations": season_data["packing_suggestions"],
        "key_travel_notes": season_data["travel_advice"]
    }
