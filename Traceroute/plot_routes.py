import json
import os
import plotly.graph_objects as go

# Load route data from JSON files
routes = []
routes_dir = "routes"

if os.path.exists(routes_dir):
    for filename in os.listdir(routes_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(routes_dir, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                routes.append(data)

if not routes:
    print("No route data found. Run traceroute.py first!")
    exit()

print(f"Found {len(routes)} routes")

# Create the map
fig = go.Figure()
colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']

for i, route in enumerate(routes):
    target = route.get('target', 'Unknown')
    hops = route.get('hops', [])
    
    # Get coordinates for this route
    lats = []
    lons = []
    texts = []
    
    for hop in hops:
        geo = hop.get('geo')
        if geo and isinstance(geo, dict) and geo.get('status') == 'success':
            lat = geo.get('lat')
            lon = geo.get('lon')
            if lat is not None and lon is not None:
                lats.append(lat)
                lons.append(lon)
                city = geo.get('city', '')
                country = geo.get('country', '')
                ip = hop.get('ip', '')
                texts.append(f"Hop {hop['hop']}: {ip}<br>{city}, {country}")
    
    if lats and lons:
        color = colors[i % len(colors)]
        
        # Add route to map
        fig.add_trace(go.Scattergeo(
            lon=lons,
            lat=lats,
            mode='lines+markers',
            line=dict(width=2, color=color),
            marker=dict(size=8, color=color),
            text=texts,
            hovertemplate='%{text}<extra></extra>',
            name=f'Route to {target}',
            showlegend=True
        ))

# Setup map appearance
fig.update_layout(
    title='Traceroute Visualization - Routes to Different Regions',
    geo=dict(
        projection_type='natural earth',
        showland=True,
        landcolor='rgb(243, 243, 243)',
        coastlinecolor='rgb(204, 204, 204)',
    ),
    height=600,
    width=1000
)

# Save as PNG image
output_png = "routes/route_map.png"
fig.write_image(output_png, width=1200, height=800, scale=2)
print(f"Route map saved as image: {output_png}")
