import googlemaps

# Replace with your Google API key
API_KEY = 'YOUR_GOOGLE_API_KEY'

# Initialize the client
gmaps = googlemaps.Client(key=API_KEY)

# Define the location you want to search around (lat, lon)
location = (40.712776, -74.005974)  # Example: New York City coordinates

# Search for places near the location within a radius (in meters)
places_result = gmaps.places_nearby(location=location, radius=1000, type='restaurant')

# Print the results
for place in places_result['results']:
    print(f"Name: {place['name']}")
    print(f"Address: {place.get('vicinity', 'No address available')}")
    print(f"Rating: {place.get('rating', 'No rating available')}")
    print('------')
