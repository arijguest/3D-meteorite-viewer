# graphs.oy

import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from IPython.display import display, HTML

def create_meteorite_chart(data):
    df = pd.DataFrame(data)
    
# Step 3: Clean and Group Similar Types
    fusion_map = {
        'L-type': ['L', 'L4', 'L5', 'L6', 'L5/6', 'L4-6', 'L6/7', 'L~5', 'L~6', 'L3.0', 'L3.2', 'L3.4', 'L3.6', 'L3.7', 'L3.8', 'L3.9', 'L3.7-6', 'L3-4', 'L3-5', 'L3-6', 'L3-7', 'L3.9-6', 'L3.7-4', 'L3.0-3.9', 'L3.3-3.7', 'L3.3-3.5', 'L4/5'],
        'H-type': ['H', 'H4', 'H5', 'H6', 'H5/6', 'H4-6', 'H3', 'H3.4', 'H3.5', 'H3.6', 'H3.7', 'H3.8', 'H3.9', 'H3-4', 'H3-5', 'H3-6', 'H3.7-6', 'H3.8-5', 'H3.9-5', 'H3.9/4', 'H4/5', 'H4-5', 'H~4', 'H~5', 'H~6'],
        'LL-type': ['LL', 'LL4', 'LL5', 'LL6', 'LL7', 'LL3', 'LL3.2', 'LL3.4', 'LL3.6', 'LL3.8', 'LL3.9', 'LL4-5', 'LL4-6', 'LL5-6', 'LL5/6', 'LL3-4', 'LL3-5', 'LL3-6', 'LL3.8-6', 'LL3.1-3.5'],
        'Carbonaceous': ['CI1', 'CM1', 'CM2', 'CR2', 'CO3', 'CO3.2', 'CO3.3', 'CO3.4', 'CO3.5', 'CO3.6', 'CV3', 'CK4', 'CK5', 'CK6', 'CK3', 'CM-an', 'CV3-an'],
        'Enstatite': ['EH', 'EH3', 'EH4', 'EH5', 'EH6', 'EH7-an', 'EL3', 'EL4', 'EL5', 'EL6', 'EL7', 'EH3/4-an'],
        'Achondrite': ['Howardite', 'Eucrite', 'Diogenite', 'Angrite', 'Aubrite', 'Acapulcoite', 'Ureilite', 'Winonaite', 'Brachinite', 'Lodranite'],
        'Iron': ['Iron', 'Iron?', 'Iron, IAB', 'Iron, IAB-MG', 'Iron, IAB-ung', 'Iron, IIAB', 'Iron, IIE', 'Iron, IIIAB', 'Iron, IVA', 'Iron, IVB', 'Iron, IID', 'Iron, IIC', 'Iron, IC', 'Iron, IC-an'],
        'Mesosiderite': ['Mesosiderite', 'Mesosiderite-A1', 'Mesosiderite-A3', 'Mesosiderite-B', 'Mesosiderite-C', 'Mesosiderite-an'],
        'Martian': ['Martian (shergottite)', 'Martian (chassignite)', 'Martian (nakhlite)', 'Martian (basaltic breccia)', 'Martian'],
        'Lunar': ['Lunar', 'Lunar (anorth)', 'Lunar (gabbro)', 'Lunar (norite)', 'Lunar (basalt)', 'Lunar (bas. breccia)', 'Lunar (feldsp. breccia)'],
        'Pallasite': ['Pallasite', 'Pallasite, PMG', 'Pallasite, PMG-an', 'Pallasite, ungrouped'],
        'Unknown': ['Unknown', 'Stone-uncl', 'Chondrite-ung'],
    }

    flattened_map = {subtype: group for group, subtypes in fusion_map.items() for subtype in subtypes}
    df['recclass_clean'] = df['recclass'].map(flattened_map).fillna('Unknown')
    meteorite_counts = df['recclass_clean'].value_counts()

    total_meteorites = meteorite_counts.sum()
    percentages = (meteorite_counts / total_meteorites * 100).round(2)

    top_classes = meteorite_counts.index[:10]
    top_counts = meteorite_counts.values[:10]
    top_percentages = percentages.values[:10]

    fig = go.Figure()
    angles = np.linspace(0, 2 * np.pi, len(top_classes), endpoint=False)

    for i, (cls, count, pct) in enumerate(zip(top_classes, top_counts, top_percentages)):
        fig.add_trace(go.Barpolar(
            r=[count],
            theta=[np.degrees(angles[i])],
            width=[360 / len(top_classes)],
            name=cls,
            hoverinfo="text",
            text=f"{cls}: {count} ({pct}%)",
            marker_color=f"hsl({(i / len(top_classes)) * 360}, 70%, 50%)",
            opacity=0.8
        ))

    fig.update_layout(
        polar=dict(
            angularaxis=dict(
                tickmode="array",
                tickvals=np.degrees(angles) + 10,
                ticktext=top_classes,
                rotation=90
            ),
            radialaxis=dict(
                visible=True,
                tickangle=45,
                tickfont_size=12,
                ticksuffix=" "
            )
        ),
        title=dict(
            text="Top Meteorite Types by Frequency",
            font=dict(family="Roboto", size=24)
        ),
        template="plotly_dark",
        font=dict(family="Roboto Mono", size=12),
        autosize=True,
        height=600
    )
    
    return fig.to_json()
