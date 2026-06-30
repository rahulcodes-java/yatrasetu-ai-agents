"""
Budget and Stay Agent (Optimized)
----------------------------------
Part of the YatraSetu AI Travel Companion system (Agents for Good track).
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

# ---------------------------------------------------------------------------
# DATA & CUSTOM DATASETS
# ---------------------------------------------------------------------------

TRIP_COST_DATA = {
    ("agra", "budget"): {
        "stay_rate": 500,
        "stay_unit": "person",  # dorm bed
        "food_rate": 300,       # per person per day
        "transport_rate": 200,  # per person per day (shared transport/auto)
        "transport_unit": "person",
        "entry_rate": 200,      # per person
        "tip": "Stay in Taj Ganj budget homestays to walk to the Taj Mahal early."
    },
    ("agra", "mid-range"): {
        "stay_rate": 2200,
        "stay_unit": "room",    # 1 room per 2 travelers
        "food_rate": 700,
        "transport_rate": 1200, # flat per day (cabs/autos)
        "transport_unit": "day",
        "entry_rate": 600,
        "tip": "Buy Taj Mahal tickets online to avoid long queues at the ticket counter."
    },
    ("agra", "premium"): {
        "stay_rate": 6500,
        "stay_unit": "room",
        "food_rate": 1800,
        "transport_rate": 3000, # flat per day (private AC sedan)
        "transport_unit": "day",
        "entry_rate": 1200,
        "tip": "Book a Taj-view room at the Oberoi Amarvilas or similar luxury stays well in advance."
    },
    ("jaipur", "budget"): {
        "stay_rate": 600,
        "stay_unit": "person",
        "food_rate": 350,
        "transport_rate": 250,
        "transport_unit": "person",
        "entry_rate": 250,
        "tip": "Rent a bicycle or use shared e-rickshaws to explore the Pink City area."
    },
    ("jaipur", "mid-range"): {
        "stay_rate": 2400,
        "stay_unit": "room",
        "food_rate": 800,
        "transport_rate": 1500,
        "transport_unit": "day",
        "entry_rate": 500,
        "tip": "Book hotels on MakeMyTrip or Booking.com 2 weeks ahead for best rates."
    },
    ("jaipur", "premium"): {
        "stay_rate": 7500,
        "stay_unit": "room",
        "food_rate": 2200,
        "transport_rate": 3500,
        "transport_unit": "day",
        "entry_rate": 1500,
        "tip": "Enjoy a royal dinner at 1135 AD inside Amer Fort for an authentic fine dining experience."
    },
    ("varanasi", "budget"): {
        "stay_rate": 450,
        "stay_unit": "person",
        "food_rate": 250,
        "transport_rate": 150,
        "transport_unit": "person",
        "entry_rate": 100,
        "tip": "Stay in hostels near Dashashwamedh Ghat to walk to the Ganga Aarti."
    },
    ("varanasi", "mid-range"): {
        "stay_rate": 2000,
        "stay_unit": "room",
        "food_rate": 600,
        "transport_rate": 1200,
        "transport_unit": "day",
        "entry_rate": 300,
        "tip": "Hire a private rowboat for the morning sunrise cruise by bargaining directly at the ghats."
    },
    ("varanasi", "premium"): {
        "stay_rate": 6000,
        "stay_unit": "room",
        "food_rate": 1500,
        "transport_rate": 2800,
        "transport_unit": "day",
        "entry_rate": 800,
        "tip": "Book a luxury heritage stay like BrijRama Palace right on the Ganga for an unmatched experience."
    },
    ("goa", "budget"): {
        "stay_rate": 800,
        "stay_unit": "person",
        "food_rate": 500,
        "transport_rate": 400,  # scooter rental is flat per day
        "transport_unit": "day",
        "entry_rate": 150,
        "tip": "Rent a scooter (₹350-₹450/day) for the cheapest way to explore beaches."
    },
    ("goa", "mid-range"): {
        "stay_rate": 3500,
        "stay_unit": "room",
        "food_rate": 1100,
        "transport_rate": 2200,
        "transport_unit": "day",
        "entry_rate": 400,
        "tip": "Book a villa/resort in Candolim or Calangute for family-friendly beach access."
    },
    ("goa", "premium"): {
        "stay_rate": 9000,
        "stay_unit": "room",
        "food_rate": 2500,
        "transport_rate": 4500,
        "transport_unit": "day",
        "entry_rate": 1000,
        "tip": "Opt for a luxury beach resort in South Goa (e.g. Varca or Cavelossim) for a quiet, premium stay."
    },
    ("munnar", "budget"): {
        "stay_rate": 600,
        "stay_unit": "person",
        "food_rate": 300,
        "transport_rate": 300,
        "transport_unit": "person",
        "entry_rate": 150,
        "tip": "Look for homestays slightly away from the main town center for affordable options."
    },
    ("munnar", "mid-range"): {
        "stay_rate": 2500,
        "stay_unit": "room",
        "food_rate": 700,
        "transport_rate": 1800,
        "transport_unit": "day",
        "entry_rate": 400,
        "tip": "Hire a local auto or jeep for sightseeing in the tea estates for a rustic experience."
    },
    ("munnar", "premium"): {
        "stay_rate": 8000,
        "stay_unit": "room",
        "food_rate": 1800,
        "transport_rate": 3500,
        "transport_unit": "day",
        "entry_rate": 1000,
        "tip": "Book a premium tea bungalow resort with valley views to experience the misty hills."
    },
    ("delhi", "budget"): {
        "stay_rate": 550,
        "stay_unit": "person",
        "food_rate": 300,
        "transport_rate": 150,
        "transport_unit": "person",
        "entry_rate": 200,
        "tip": "Use the Delhi Metro Tourist Card (1-day or 3-day) for unlimited cheap transit."
    },
    ("delhi", "mid-range"): {
        "stay_rate": 2800,
        "stay_unit": "room",
        "food_rate": 850,
        "transport_rate": 1500,
        "transport_unit": "day",
        "entry_rate": 500,
        "tip": "Stay in Central or South Delhi (like Connaught Place or Saket) for safe and easy commute."
    },
    ("delhi", "premium"): {
        "stay_rate": 8500,
        "stay_unit": "room",
        "food_rate": 2200,
        "transport_rate": 3500,
        "transport_unit": "day",
        "entry_rate": 1200,
        "tip": "Book a heritage hotel in Lutyens' Delhi or a 5-star stay in Chanakyapuri."
    },
    ("mumbai", "budget"): {
        "stay_rate": 750,
        "stay_unit": "person",
        "food_rate": 350,
        "transport_rate": 200,
        "transport_unit": "person",
        "entry_rate": 200,
        "tip": "Use local trains and black-and-yellow autos (in suburbs) or share-taxis."
    },
    ("mumbai", "mid-range"): {
        "stay_rate": 3800,
        "stay_unit": "room",
        "food_rate": 1000,
        "transport_rate": 1800,
        "transport_unit": "day",
        "entry_rate": 500,
        "tip": "Stay near Bandra or Andheri for a balance of transit convenience and lively eateries."
    },
    ("mumbai", "premium"): {
        "stay_rate": 10500,
        "stay_unit": "room",
        "food_rate": 2600,
        "transport_rate": 4000,
        "transport_unit": "day",
        "entry_rate": 1200,
        "tip": "Enjoy sea-facing rooms in Colaba or Nariman Point, and dine at fine restaurants in Bandra."
    },
    ("rishikesh", "budget"): {
        "stay_rate": 500,
        "stay_unit": "person",
        "food_rate": 300,
        "transport_rate": 200,
        "transport_unit": "person",
        "entry_rate": 150,
        "tip": "Stay in shared dorms in Tapovan, the backpacker hub with plenty of cafes."
    },
    ("rishikesh", "mid-range"): {
        "stay_rate": 2200,
        "stay_unit": "room",
        "food_rate": 700,
        "transport_rate": 1300,
        "transport_unit": "day",
        "entry_rate": 400,
        "tip": "Look for hotels or yoga retreats near Laxman Jhula or Ram Jhula for peaceful vibes."
    },
    ("rishikesh", "premium"): {
        "stay_rate": 7000,
        "stay_unit": "room",
        "food_rate": 1800,
        "transport_rate": 3000,
        "transport_unit": "day",
        "entry_rate": 1000,
        "tip": "Book a premium wellness resort along the Ganges in Shivpuri or Narendra Nagar."
    }
}

STAY_AREAS = {
    "agra": {
        "budget": [
            {"area": "Taj Ganj (East Gate)", "type_solo": "Backpacker Hostel Dorms", "type_couple": "Cozy Private Homestays", "type_family": "Budget Family Guesthouses", "type_group": "Group Dormitories/Guesthouses", "desc": "Walking distance to Taj Mahal. Perfect for sunrise visits.", "platform": "Hostelworld / Booking.com"},
            {"area": "Fatehabad Road", "type_solo": "Pod Hostels", "type_couple": "Standard Double Rooms", "type_family": "Budget Hotels with Family Rooms", "type_group": "Shared Rooms in Budget Hotels", "desc": "Lively street with cheap local eateries.", "platform": "Booking.com / Agoda"},
            {"area": "Sadar Bazar Area", "type_solo": "Railway Retiring Rooms / Homestays", "type_couple": "Local Heritage Homestays", "type_family": "Spacious Homestays", "type_group": "Multi-bed Guesthouse Rooms", "desc": "Near Agra Cantt station; excellent street food nearby.", "platform": "Airbnb / MakeMyTrip"}
        ],
        "mid-range": [
            {"area": "Fatehabad Road", "type_solo": "Boutique Hotel Single Rooms", "type_couple": "3-Star Hotels with Pool", "type_family": "Family Suites in 3-Star Hotels", "type_group": "Connecting Rooms in 3-Star Hotels", "desc": "Safe, tourist-friendly sector with excellent security.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Taj Ganj", "type_solo": "Private Rooms in Heritage Homestays", "type_couple": "Rooftop Taj-View Boutique Hotels", "type_family": "Heritage Homestay Apartments", "type_group": "Entire Heritage Guesthouses", "desc": "Cultural experience with stunning rooftop dining views.", "platform": "Airbnb / Booking.com"},
            {"area": "Cantonment Area", "type_solo": "Executive Business Hotels", "type_couple": "Quiet Garden Bungalows", "type_family": "Spacious 3-Star Hotel Rooms", "type_group": "Suite Rooms", "desc": "Peaceful, green locality near the railway station.", "platform": "MakeMyTrip / Agoda"}
        ],
        "premium": [
            {"area": "Taj East Gate Road", "type_solo": "Luxury Hotel Club Rooms", "type_couple": "5-Star Resorts with Taj Views", "type_family": "Luxury Family Suites", "type_group": "Multiple Club Rooms in Resorts", "desc": "Ultra-luxury resorts with private golf cart service to the monument.", "platform": "Direct Booking / Booking.com"},
            {"area": "Fatehabad Road (Premium)", "type_solo": "5-Star Business Suites", "type_couple": "High-end Heritage Suites", "type_family": "Luxury Connecting Suites", "type_group": "Multi-room Luxury Penthouse", "desc": "Top-tier hospitality with fine dining and rooftop pools.", "platform": "MakeMyTrip / Agoda"},
            {"area": "Shamshabad Road", "type_solo": "Secluded Spa Resort Rooms", "type_couple": "Private Luxury Villas", "type_family": "Premium Multi-bedroom Villas", "type_group": "Entire Premium Villa", "desc": "Quiet, exclusive resort properties with expansive lawns.", "platform": "Airbnb / Luxury Platforms"}
        ]
    },
    "jaipur": {
        "budget": [
            {"area": "Pink City (Old City)", "type_solo": "Social Hostels", "type_couple": "Budget Heritage Rooms", "type_family": "Local Family Homestays", "type_group": "Hostel Dorm Group Blocks", "desc": "Near Hawa Mahal and Johri Bazar. Vibrant and traditional.", "platform": "Hostelworld / Booking.com"},
            {"area": "Sindhi Camp", "type_solo": "Transit Hostels / Pods", "type_couple": "Budget Double Rooms", "type_family": "Budget Family Hotels", "type_group": "Shared Budget Hotel Rooms", "desc": "Close to the main bus stand and metro station.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "C-Scheme (Budget)", "type_solo": "Backpacker Cafes with Dorms", "type_couple": "Private Rooms in Guesthouses", "type_family": "Homestay Apartments", "type_group": "Group Homestays", "desc": "Upscale area with budget options; very safe for night walks.", "platform": "Airbnb"}
        ],
        "mid-range": [
            {"area": "C-Scheme", "type_solo": "Boutique Studio Apartments", "type_couple": "Trendy Boutique Hotels", "type_family": "Serviced Apartments", "type_group": "Boutique Hotel Suites", "desc": "Jaipur's trendiest hub with chic cafes and restaurants.", "platform": "Booking.com / Airbnb"},
            {"area": "Bani Park", "type_solo": "Heritage Hotel Single Rooms", "type_couple": "Traditional Heritage Haveli Hotels", "type_family": "Heritage Family Suites", "type_group": "Haveli Rooms Group Booking", "desc": "Beautiful old mansions converted into charming hotels with gardens.", "platform": "MakeMyTrip / Booking.com"},
            {"area": "Malviya Nagar", "type_solo": "Modern Business Hotels", "type_couple": "Cozy Studio Stays", "type_family": "3-Star Family Hotels", "type_group": "Connecting Business Rooms", "desc": "Close to shopping malls and Jaipur Airport.", "platform": "Agoda / MakeMyTrip"}
        ],
        "premium": [
            {"area": "Rambagh / Tonk Road", "type_solo": "Heritage Palace Single Suites", "type_couple": "Luxury Palace Hotels", "type_family": "Palace Royal Family Suites", "type_group": "Luxury Multi-room Suites", "desc": "Experience true royal Rajput hospitality in historic palaces.", "platform": "Direct Booking / Booking.com"},
            {"area": "Kukas (Outskirts)", "type_solo": "Premium Wellness Retreat Rooms", "type_couple": "Luxury Fort-Style Resorts", "type_family": "Luxury Villas with Private Pools", "type_group": "Resort Cottages Group", "desc": "Grand fort-style resort properties in the Aravalli hills.", "platform": "MakeMyTrip / Agoda"},
            {"area": "Bani Park (Premium)", "type_solo": "Grand Haveli Suites", "type_couple": "Premium Heritage Haveli Suites", "type_family": "Grand Family Haveli Suites", "type_group": "Private Haveli Block", "desc": "Top-tier heritage hospitality with traditional Rajasthani character.", "platform": "Booking.com"}
        ]
    },
    "varanasi": {
        "budget": [
            {"area": "Dashashwamedh Ghat", "type_solo": "Backpacker Hostels", "type_couple": "Simple Ghat-view Guesthouses", "type_family": "Traditional Family Homestays", "type_group": "Dormitory Blocks near Ghats", "desc": "Steps away from the main Ganga Aarti venue.", "platform": "Hostelworld / Booking.com"},
            {"area": "Assi Ghat (Budget)", "type_solo": "Social Cafe-Hostels", "type_couple": "Budget Double Rooms", "type_family": "Assi Homestays", "type_group": "Group Dorm Rooms", "desc": "Backpacker-friendly area with a relaxed vibe and cultural music.", "platform": "Booking.com / Airbnb"},
            {"area": "Varanasi Junction Area", "type_solo": "Transit Lodges", "type_couple": "Standard Station Hotels", "type_family": "Family Station Guesthouses", "type_group": "Shared Station Lodges", "desc": "Convenient for early/late train arrivals; crowded but cheap.", "platform": "MakeMyTrip"}
        ],
        "mid-range": [
            {"area": "Assi Ghat", "type_solo": "Boutique Heritage Rooms", "type_couple": "Cozy Ghat-side Heritage Hotels", "type_family": "Family Rooms in Heritage Hotels", "type_group": "Multi-room Heritage Guesthouses", "desc": "Artistic, cleaner end of Varanasi; great yoga centers.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Cantonment Area", "type_solo": "Modern Business Hotels", "type_couple": "3-Star Chain Hotels", "type_family": "Family Suites in 3-Star Hotels", "type_group": "Connecting Chain Rooms", "desc": "Peaceful, wide roads, far from the chaotic narrow ghat lanes.", "platform": "MakeMyTrip / Agoda"},
            {"area": "Dashashwamedh Ghat (Mid)", "type_solo": "Comfortable Guesthouse Rooms", "type_couple": "Boutique River-View Hotels", "type_family": "River-View Family Suites", "type_group": "Comfortable Heritage Rooms", "desc": "Heart of old city, requires walking through narrow alleys.", "platform": "Booking.com / Airbnb"}
        ],
        "premium": [
            {"area": "Nadesar / Cantonment", "type_solo": "Luxury Palace Club Rooms", "type_couple": "Historic Palace Hotels", "type_family": "Palace Family Suites", "type_group": "Luxury Palace Wings", "desc": "Ultra-exclusive heritage properties with royal gardens.", "platform": "Direct Booking"},
            {"area": "Ghats (Premium)", "type_solo": "Luxury Riverfront Heritage Rooms", "type_couple": "Luxury Heritage Hotels on Ghats", "type_family": "Ghat-view Luxury Family Suites", "type_group": "Private Ghat-side Suites", "desc": "Top-tier heritage hotels with private boat services and aarti access.", "platform": "Booking.com / Direct"},
            {"area": "Sarnath Road (Premium)", "type_solo": "Premium Wellness Retreats", "type_couple": "Premium Garden Resorts", "type_family": "Luxury Garden Villas", "type_group": "Resort Cottages Group", "desc": "Peaceful premium stays near Buddhist stupas, away from city noise.", "platform": "MakeMyTrip / Agoda"}
        ]
    },
    "goa": {
        "budget": [
            {"area": "Anjuna / Vagator", "type_solo": "Party Hostels", "type_couple": "Budget Beach Huts", "type_family": "Budget Homestay Cottages", "type_group": "Hostel Dorm Dorms Group", "desc": "Backpacker hub, cheap bike rental, lively night markets.", "platform": "Hostelworld / Booking.com"},
            {"area": "Arambol", "type_solo": "Social Hostel Dorms", "type_couple": "Eco Beach Shacks", "type_family": "Quiet Budget Guesthouses", "type_group": "Group Beach Huts", "desc": "Relaxed bohemian crowd, sweet water lake, drum circles.", "platform": "Booking.com / Airbnb"},
            {"area": "Panaji (Fontainhas)", "type_solo": "Portuguese Heritage Hostels", "type_couple": "Budget Heritage Rooms", "type_family": "Heritage Homestays", "type_group": "Heritage Dorms Group", "desc": "Latin Quarter with colorful streets, cafes, and historic vibe.", "platform": "Airbnb / Booking.com"}
        ],
        "mid-range": [
            {"area": "Candolim / Calangute", "type_solo": "Boutique Guest Rooms", "type_couple": "3-Star Beach Resorts", "type_family": "Family Beach Resorts with Pools", "type_group": "Connecting Resort Rooms", "desc": "Highly commercialized, family-friendly, watersports hub.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Palolem / Patnem", "type_solo": "Comfort Beach Bungalows", "type_couple": "Sea-view Coco Huts", "type_family": "Family Beach Cottages", "type_group": "Cottage Clusters", "desc": "Beautiful crescent beach, clean waters, scenic sunset views.", "platform": "Booking.com / Agoda"},
            {"area": "Fontainhas (Panaji)", "type_solo": "Heritage Hotel Rooms", "type_couple": "Portuguese Boutique Heritage Hotels", "type_family": "Heritage Villa Apartments", "type_group": "Entire Heritage House", "desc": "Colonial-era boutique hotels in a culturally rich neighborhood.", "platform": "Airbnb / Booking.com"}
        ],
        "premium": [
            {"area": "South Goa Beaches (Varca/Cavelossim)", "type_solo": "Luxury Spa Resort Rooms", "type_couple": "5-Star Beachfront Resorts", "type_family": "Luxury Family Beach Villas", "type_group": "Premium Multi-room Villas", "desc": "Pristine white sand beaches, quiet atmosphere, high-end dining.", "platform": "Direct Booking / Booking.com"},
            {"area": "Sinquerim / Candolim", "type_solo": "5-Star Resort Club Rooms", "type_couple": "Luxury Cliff-top Resorts", "type_family": "Luxury Family Resort Suites", "type_group": "Multiple Luxury Suites", "desc": "Overlooking the Arabian Sea, near historic Fort Aguada.", "platform": "MakeMyTrip / Booking.com"},
            {"area": "Aldona / Assagao (Inland)", "type_solo": "Luxury Heritage Villa Rooms", "type_couple": "Restored Portuguese Luxury Villas", "type_family": "Private Luxury Villa Estates", "type_group": "Entire Luxury Villa Estate", "desc": "Lush green heritage villages, private pools, quiet luxury.", "platform": "Airbnb / Luxury Platforms"}
        ]
    },
    "munnar": {
        "budget": [
            {"area": "Munnar Town Area", "type_solo": "Backpacker Homestays", "type_couple": "Budget Double Rooms", "type_family": "Budget Family Homestays", "type_group": "Group Dorm Homestays", "desc": "Near bus station and local markets. Easy for public transport.", "platform": "MakeMyTrip / Booking.com"},
            {"area": "Old Munnar", "type_solo": "Social Hostel Dorms", "type_couple": "Budget Guesthouse Rooms", "type_family": "Budget Guesthouses", "type_group": "Group Guesthouse Rooms", "desc": "Slightly quieter than town; walking trails nearby.", "platform": "Booking.com"},
            {"area": "Anachal (Budget)", "type_solo": "Shared Homestays", "type_couple": "Budget Hillside Cottages", "type_family": "Hillside Family Guesthouses", "type_group": "Hillside Group Rooms", "desc": "15 km from Munnar town, cheaper rates, scenic valley paths.", "platform": "Airbnb / Booking.com"}
        ],
        "mid-range": [
            {"area": "Devikulam Road / Chithirapuram", "type_solo": "Boutique Hilltop Rooms", "type_couple": "Cozy Hill-view Resorts", "type_family": "3-Star Family Hill Resorts", "type_group": "Resort Cottages Group", "desc": "Scenic and peaceful valley views, tea plantation walks.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Pallivasal", "type_solo": "Tea Estate Homestay Rooms", "type_couple": "Waterfall-view Boutique Resorts", "type_family": "Family Suite Cottages", "type_group": "Cottage Blocks", "desc": "Stunning views of Pallivasal waterfalls and tea gardens.", "platform": "Booking.com / Agoda"},
            {"area": "Anachal", "type_solo": "Boutique Forest Rooms", "type_couple": "Mid-range Valley Resorts", "type_family": "Spacious Valley Villas", "type_group": "Entire Valley Villa", "desc": "Comfortable family resorts with spice garden tours.", "platform": "Airbnb / MakeMyTrip"}
        ],
        "premium": [
            {"area": "Chinnakanal / Suryanelli", "type_solo": "Premium Lake-view Rooms", "type_couple": "Luxury Resorts with Private Jacuzzi", "type_family": "Luxury Multi-bedroom Villas", "type_group": "Luxury Villa Estates", "desc": "Near Anaerangal Lake. Misty hills, luxury villas, jeep safaris.", "platform": "Direct Booking / Booking.com"},
            {"area": "Pallivasal / Tea Estates", "type_solo": "Premium Tea Bungalow Suites", "type_couple": "Luxury Tea Bungalow Resorts", "type_family": "Luxury Tea Estate Bungalows", "type_group": "Private Tea Estate Bungalow", "desc": "Historic British-era tea bungalows with personalized butler service.", "platform": "Direct Booking"},
            {"area": "Munnar Bypass Road", "type_solo": "Premium Valley Suites", "type_couple": "Luxury Treehouse Resorts", "type_family": "Premium Treehouses & Villas", "type_group": "Treehouse Resort Group", "desc": "Luxury treehouses set in dense canopy with views of tea valleys.", "platform": "MakeMyTrip / Agoda"}
        ]
    },
    "delhi": {
        "budget": [
            {"area": "Paharganj", "type_solo": "Backpacker Hostels", "type_couple": "Budget Double Rooms", "type_family": "Budget Family Hotels", "type_group": "Hostel Dorm Group Blocks", "desc": "Right next to New Delhi Railway Station; very cheap food.", "platform": "Hostelworld / Booking.com"},
            {"area": "Connaught Place (Budget)", "type_solo": "Social Pod Hostels", "type_couple": "Budget Guest Rooms", "type_family": "Budget Guesthouses", "type_group": "Shared Pod Rooms", "desc": "Central Delhi location, walking distance to metro hub.", "platform": "Booking.com"},
            {"area": "Majnu ka Tilla", "type_solo": "Tibetan Guest Houses", "type_couple": "Tibetan Guesthouse Rooms", "type_family": "Family Guesthouses", "type_group": "Group Guesthouse Rooms", "desc": "Delhi's Little Tibet; peaceful cafes, great food, cheap rates.", "platform": "Booking.com / Airbnb"}
        ],
        "mid-range": [
            {"area": "Connaught Place (CP)", "type_solo": "Boutique Executive Rooms", "type_couple": "3-Star Boutique Hotels", "type_family": "Serviced Apartments", "type_group": "CP Hotel Suites", "desc": "Heart of Delhi. Heritage buildings, shopping, and dining.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Karol Bagh", "type_solo": "Business Hotel Rooms", "type_couple": "Comfortable 3-Star Hotels", "type_family": "Spacious Family Rooms", "type_group": "Connecting Hotel Rooms", "desc": "Busy shopping district with excellent metro connectivity.", "platform": "MakeMyTrip / Agoda"},
            {"area": "South Delhi (Greater Kailash/Saket)", "type_solo": "Cozy Studio Homestays", "type_couple": "Chic Boutique B&Bs", "type_family": "Serviced Family Apartments", "type_group": "Entire Serviced Apartment", "desc": "Safe, green residential areas close to malls and monuments.", "platform": "Airbnb / Booking.com"}
        ],
        "premium": [
            {"area": "Chanakyapuri / Lutyens' Delhi", "type_solo": "5-Star Club Rooms", "type_couple": "5-Star Historic Hotels", "type_family": "Grand Family Suites", "type_group": "Multiple Club Rooms", "desc": "Diplomatic enclave, elite dining, absolute safety, and gardens.", "platform": "Direct Booking"},
            {"area": "Aerocity", "type_solo": "5-Star Transit Suites", "type_couple": "Luxury Business/Spa Hotels", "type_family": "Aerocity Luxury Family Suites", "type_group": "Luxury Business Wings", "desc": "Modern luxury hub near Delhi Airport. Fine dining and bars.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "South Delhi (Vasant Kunj)", "type_solo": "Premium Boutique Suites", "type_couple": "Luxury Boutique Hotels", "type_family": "Luxury Villa Apartments", "type_group": "Entire Luxury Villa", "desc": "Upscale green neighborhood, high-end shopping and dining.", "platform": "Booking.com"}
        ]
    },
    "mumbai": {
        "budget": [
            {"area": "Colaba / Fort (Budget)", "type_solo": "Backpacker Hostels", "type_couple": "Budget Double Rooms", "type_family": "Simple Family Guesthouses", "type_group": "Hostel Dorm Group Blocks", "desc": "South Mumbai heritage area, walking distance to Gateway of India.", "platform": "Hostelworld / Booking.com"},
            {"area": "Andheri East (Budget)", "type_solo": "Transit Pod Hostels", "type_couple": "Budget Double Rooms", "type_family": "Simple Family Lodges", "type_group": "Shared Pod Rooms", "desc": "Close to metro lines and Mumbai airport.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Bandra West (Budget)", "type_solo": "Social Hostel Dorms", "type_couple": "Small Guesthouse Rooms", "type_family": "Budget Homestays", "type_group": "Shared Guesthouse Rooms", "desc": "Trendy suburb, cheap street food, youth culture, beach walks.", "platform": "Airbnb / Hostelworld"}
        ],
        "mid-range": [
            {"area": "Bandra West", "type_solo": "Boutique Studio Stays", "type_couple": "Chic Boutique Hotels", "type_family": "Serviced Apartments", "type_group": "Boutique Hotel Suites", "desc": "Queen of suburbs. Cafes, restaurants, Bollywood sightings.", "platform": "Booking.com / Airbnb"},
            {"area": "Juhu", "type_solo": "Sea-view Guest Rooms", "type_couple": "3-Star Beach Hotels", "type_family": "Family Beach Hotels", "type_group": "Connecting Beach Rooms", "desc": "Near Juhu Beach, residential feel with beach access.", "platform": "MakeMyTrip / Agoda"},
            {"area": "Fort / Kala Ghoda", "type_solo": "Executive Heritage Rooms", "type_couple": "Boutique Art Hotels", "type_family": "Heritage Family Suites", "type_group": "Heritage Suite Rooms", "desc": "Mumbai's art district, heritage buildings, art cafes.", "platform": "Booking.com / MakeMyTrip"}
        ],
        "premium": [
            {"area": "Colaba / Marine Drive", "type_solo": "Luxury Sea-view Suites", "type_couple": "5-Star Sea-facing Heritage Hotels", "type_family": "Grand Sea-facing Suites", "type_group": "Multiple Sea-view Rooms", "desc": "Iconic views of Marine Drive and Gateway of India.", "platform": "Direct Booking"},
            {"area": "Juhu (Premium)", "type_solo": "Luxury Beach Club Rooms", "type_couple": "5-Star Juhu Beach Resorts", "type_family": "Luxury Beach Villas", "type_group": "Resort Cottages Group", "desc": "Beachfront luxury, celebrity-frequented fine dining.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Bandra Kurla Complex (BKC)", "type_solo": "Luxury Business Suites", "type_couple": "Contemporary 5-Star Hotels", "type_family": " BKC Luxury Family Suites", "type_group": "BKC Luxury Wings", "desc": "Modern luxury business district, top-end restaurants.", "platform": "MakeMyTrip / Agoda"}
        ]
    },
    "rishikesh": {
        "budget": [
            {"area": "Tapovan", "type_solo": "Backpacker Cafes & Hostels", "type_couple": "Budget Double Rooms", "type_family": "Budget Family Homestays", "type_group": "Hostel Dorm Group Blocks", "desc": "Backpacker hub, cafes, yoga classes, rafting bookings.", "platform": "Hostelworld / Booking.com"},
            {"area": "Laxman Jhula (Budget)", "type_solo": "Social Hostel Dorms", "type_couple": "Ganges-view Budget Rooms", "type_family": "Ghat-side Guesthouses", "type_group": "Group Dorm Rooms", "desc": "Overlooking the Ganges, lively ashram district.", "platform": "Booking.com"},
            {"area": "Ram Jhula / Swarg Ashram", "type_solo": "Ashram Stay Dorms", "type_couple": "Ashram Private Rooms", "type_family": "Ashram Family Rooms", "type_group": "Shared Ashram Rooms", "desc": "Very peaceful, vegetarian food, spiritual ashram vibes.", "platform": "Direct / Booking.com"}
        ],
        "mid-range": [
            {"area": "Tapovan (Mid-range)", "type_solo": "Boutique Retreat Rooms", "type_couple": "Yoga Retreats & Boutique Hotels", "type_family": "Yoga Family Resorts", "type_group": "Retreat Cottages Group", "desc": "Modern comfort, cafe scene, spa treatments.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Ram Jhula / Swarg Ashram", "type_solo": "Comfort Ashram Rooms", "type_couple": "Boutique Heritage Hotels", "type_family": "Heritage Family Suites", "type_group": "Heritage Suite Rooms", "desc": "Near Ganga river walk and Beatles Ashram.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Shivpuri (Mid-range)", "type_solo": "Boutique Rafting Camps", "type_couple": "Comfort Rafting Camps", "type_family": "Family Camping Tents", "type_group": "Shared Camping Tents", "desc": "16 km upstream, river rafting hub, riverside camping.", "platform": "MakeMyTrip"}
        ],
        "premium": [
            {"area": "Shivpuri / Narendra Nagar", "type_solo": "Luxury Wellness Suites", "type_couple": "5-Star Spa Resorts in Hills", "type_family": "Luxury Mountain Villas", "type_group": "Resort Cottages Group", "desc": "Ultra-luxury spa retreats overlooking the Ganges valley.", "platform": "Direct Booking"},
            {"area": "Tapovan / Ganges Banks", "type_solo": "Luxury Riverfront Club Rooms", "type_couple": "5-Star Riverfront Resorts", "type_family": "Luxury Riverfront Suites", "type_group": "Multiple Riverfront Rooms", "desc": "Private beach access, yoga pavilions, luxury fine dining.", "platform": "Booking.com / MakeMyTrip"},
            {"area": "Swarg Ashram (Premium)", "type_solo": "Premium Ashram Suites", "type_couple": "Luxury Heritage Ashram Stays", "type_family": "Premium Heritage Suites", "type_group": "Private Ashram Suites", "desc": "Exclusive, peaceful spiritual luxury stays with private ghats.", "platform": "Direct Booking"}
        ]
    }
}

# ---------------------------------------------------------------------------
# DETERMINISTIC PYTHON TOOLS
# ---------------------------------------------------------------------------

def estimate_trip_cost(destination: str, days: int, travelers: int, budget_tier: str) -> str:
    """Use this tool FIRST whenever the user asks about budget, costs, or trip expenses.
Returns a complete formatted cost breakdown for the given destination, duration,
traveler count, and budget tier. Call this before invoking the search sub-agent.

    Args:
        destination: The destination city (e.g. Agra, Jaipur, Delhi, Mumbai).
        days: Trip duration in number of days.
        travelers: Number of travelers.
        budget_tier: Budget preference ('budget', 'mid-range', or 'premium').
    """
    clean_dest = destination.strip().lower()
    clean_tier = budget_tier.strip().lower()
    
    # Normalize budget tier
    if "budget" in clean_tier:
        norm_tier = "budget"
    elif "mid" in clean_tier:
        norm_tier = "mid-range"
    elif "prem" in clean_tier:
        norm_tier = "premium"
    else:
        norm_tier = "mid-range"  # Default fallback
        
    supported_dests = ["agra", "jaipur", "varanasi", "goa", "munnar", "delhi", "mumbai", "rishikesh"]
    note = ""
    if clean_dest not in supported_dests:
        note = f"*[Note: Estimates for '{destination}' are not in our local database. Using default estimates based on Delhi.]*\n\n"
        clean_dest = "delhi"
        
    cost_info = TRIP_COST_DATA[(clean_dest, norm_tier)]
    
    # Calculate Accommodation Cost
    stay_rate = cost_info["stay_rate"]
    stay_unit = cost_info["stay_unit"]
    if stay_unit == "person":
        stay_cost = stay_rate * travelers * days
        stay_desc = f"₹{stay_rate:,}/person/night × {travelers} × {days} = ₹{stay_cost:,}"
    else:
        rooms = (travelers + 1) // 2
        stay_cost = stay_rate * rooms * days
        room_str = f" × {rooms} room{'s' if rooms > 1 else ''}" if rooms > 1 else ""
        stay_desc = f"₹{stay_rate:,}/night{room_str} × {days} = ₹{stay_cost:,}"
        
    # Calculate Food Cost
    food_rate = cost_info["food_rate"]
    food_cost = food_rate * travelers * days
    food_desc = f"₹{food_rate:,}/person/day × {travelers} × {days} = ₹{food_cost:,}"
    
    # Calculate Transport Cost
    transport_rate = cost_info["transport_rate"]
    transport_unit = cost_info["transport_unit"]
    if transport_unit == "person":
        transport_cost = transport_rate * travelers * days
        transport_desc = f"₹{transport_rate:,}/person/day × {travelers} × {days} = ₹{transport_cost:,}"
    else:
        transport_cost = transport_rate * days
        transport_desc = f"₹{transport_rate:,}/day × {days} = ₹{transport_cost:,}"
        
    # Calculate Entry Tickets Cost
    entry_rate = cost_info["entry_rate"]
    entry_cost = entry_rate * travelers
    entry_desc = f"₹{entry_rate:,}/person × {travelers} = ₹{entry_cost:,}"
    
    # Total
    total = stay_cost + food_cost + transport_cost + entry_cost
    
    formatted_str = (
        f"{note}"
        f"📍 Destination: {destination.strip().title()} | {days} Day{'s' if days > 1 else ''} | {travelers} Traveler{'s' if travelers > 1 else ''} | {norm_tier.title()}\n"
        f"🏨 Stay:         {stay_desc}\n"
        f"🍽️  Food:         {food_desc}\n"
        f"🚗 Transport:    {transport_desc}\n"
        f"🎟️  Entry Tickets: {entry_desc}\n"
        f"💰 Total Estimate: ₹{total:,}\n"
        f"💡 Tip: {cost_info['tip']}"
    )
    return formatted_str


def get_stay_recommendations(destination: str, budget_tier: str, companions: str) -> str:
    """Use this to recommend stay areas and accommodation types for a destination and budget
tier. Call this alongside or after estimate_trip_cost. Only invoke search_sub_agent
if the user specifically asks for current prices or live availability.

    Args:
        destination: The destination city (e.g. Agra, Jaipur, Delhi, Mumbai).
        budget_tier: Budget preference ('budget', 'mid-range', or 'premium').
        companions: Travel companions ('solo', 'couple', 'family', or 'group').
    """
    clean_dest = destination.strip().lower()
    clean_tier = budget_tier.strip().lower()
    clean_comp = companions.strip().lower()
    
    # Normalize budget tier
    if "budget" in clean_tier:
        norm_tier = "budget"
    elif "mid" in clean_tier:
        norm_tier = "mid-range"
    elif "prem" in clean_tier:
        norm_tier = "premium"
    else:
        norm_tier = "mid-range"
        
    # Normalize companions
    if "solo" in clean_comp:
        comp_type = "solo"
    elif "couple" in clean_comp or "partner" in clean_comp or "spouse" in clean_comp:
        comp_type = "couple"
    elif "family" in clean_comp or "kid" in clean_comp or "parent" in clean_comp:
        comp_type = "family"
    elif "group" in clean_comp or "friend" in clean_comp or "colleague" in clean_comp:
        comp_type = "group"
    else:
        comp_type = "solo"
        
    supported_dests = ["agra", "jaipur", "varanasi", "goa", "munnar", "delhi", "mumbai", "rishikesh"]
    note = ""
    if clean_dest not in supported_dests:
        note = f"*[Note: Recommendations for '{destination}' are not in our local database. Showing defaults for Delhi.]*\n\n"
        clean_dest = "delhi"
        
    stays = STAY_AREAS[clean_dest][norm_tier]
    
    formatted_stays = [
        f"{note}📍 Accommodation Recommendations for {destination.strip().title()} | {norm_tier.title()} | Companions: {comp_type.title()}\n"
    ]
    for i, stay in enumerate(stays, 1):
        stay_type = stay.get(f"type_{comp_type}", stay["type_solo"])
        formatted_stays.append(
            f"{i}. Area: {stay['area']}\n"
            f"   🏨 Stay Type: {stay_type}\n"
            f"   🔍 Details: {stay['desc']}\n"
            f"   💡 Booking Tip: Use {stay['platform']} to secure the best rates.\n"
        )
    return "\n".join(formatted_stays)

# ---------------------------------------------------------------------------
# SUB-AGENT: SEARCH SPECIALIST (SINGLE-QUERY ONLY)
# ---------------------------------------------------------------------------

search_sub_agent = Agent(
    model="gemini-2.5-flash",
    name="search_sub_agent",
    description=(
        "Searches the web for current hotel prices, live availability, or specific "
        "travel expenses not covered by deterministic tools."
    ),
    instruction="""
You will receive a single, specific question.
Answer it in 2-3 sentences using google_search.
Do not ask follow-up questions or do multi-step reasoning.
""",
    tools=[google_search],
)

# ---------------------------------------------------------------------------
# MAIN BUDGET & STAY AGENT
# ---------------------------------------------------------------------------

root_agent = Agent(
    model="gemini-2.5-flash",
    name="budget_and_stay_agent",
    description=(
        "Provides structured cost breakdowns and accommodation/area recommendations "
        "for popular destinations in India based on budget tiers."
    ),
    instruction="""
You are the Budget & Stay Agent for YatraSetu, a travel companion app designed to help first-time and budget travelers explore India safely, comfortably, and economically.

Your primary role is to provide a realistic, trustworthy cost breakdown and stay recommendations so travelers can plan without financial surprises.

Follow these execution guidelines:
1. Gather Inputs:
   Check if the user has provided:
   - Destination(s)
   - Number of days for the trip
   - Number of travelers
   - Budget tier (budget / mid-range / premium) OR total budget in INR
   - Travel companions (solo / couple / family / group)
   
   If the user specified a total budget in INR instead of a tier, map it to a budget tier:
   - Low budget (under ₹1,500 per day per traveler): "budget"
   - Moderate budget (₹1,500 to ₹5,000 per day per traveler): "mid-range"
   - High budget (above ₹5,000 per day per traveler): "premium"

   If any of these details are missing, ask the user politely to provide all missing details in a single message before calling any tool.

2. Tool Calling (Strict Order):
   - Always call `estimate_trip_cost` first.
   - Then call `get_stay_recommendations`.
   - Only invoke the search_sub_agent if the user specifically asks for current hotel prices, live availability, or information not covered by those two tools. Never use search to confirm or reformat what a Python tool already returned.

3. Output Format:
   Present the results in this structure:
   - **Cost Breakdown**: Present the output of `estimate_trip_cost` exactly as returned (do not reformat it).
   - **Stay Recommendations**: Present the output of `get_stay_recommendations` exactly as returned.
   - **Money-Saving Tips**: Add 2-3 lines of practical money-saving tips specific to the destination and budget tier.
   Keep your total response under 400 words.

4. Tone:
   Maintain a friendly, practical, and helpful tone, like a local resident who is planning a trip for a dear friend. If a destination is expensive (e.g. Mumbai, Goa) and the user's budget is tight, flag it politely and suggest cheaper alternatives.
""",
    tools=[
        AgentTool(agent=search_sub_agent),
        estimate_trip_cost,
        get_stay_recommendations,
    ],
)
