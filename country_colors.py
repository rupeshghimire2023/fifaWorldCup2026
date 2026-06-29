COUNTRY_COLORS = {
    "South Africa": {"primary": "#007A4D", "secondary": "#FFB612"},  # Green and Gold
    "Canada": {"primary": "#FF0000", "secondary": "#FFFFFF"},  # Red and White
    "Germany": {"primary": "#000000", "secondary": "#DD0000"},  # Black, Red, Gold
    "Paraguay": {"primary": "#D52B1E", "secondary": "#0038A8"},  # Red, White, Blue
    "Netherlands": {"primary": "#FF4F00", "secondary": "#FFFFFF"},  # Orange and White
    "Morocco": {"primary": "#C1272D", "secondary": "#006233"},  # Red and Green
    "Brazil": {"primary": "#009739", "secondary": "#FEDD00"},  # Green and Yellow
    "Japan": {"primary": "#BC002D", "secondary": "#FFFFFF"},  # Red and White
    "Ivory Coast": {"primary": "#FF7900", "secondary": "#009E60"},  # Orange, White, Green
    "Norway": {"primary": "#BA0C2F", "secondary": "#00205B"},  # Red, White, Blue
    "France": {"primary": "#0055A4", "secondary": "#EF4135"},  # Blue, White, Red
    "Sweden": {"primary": "#006AA7", "secondary": "#FECC00"},  # Blue and Yellow
    "Mexico": {"primary": "#006847", "secondary": "#CE1126"},  # Green, White, Red
    "Ecuador": {"primary": "#FFD100", "secondary": "#034EA2"},  # Yellow, Blue, Red
    "England": {"primary": "#C8102E", "secondary": "#FFFFFF"},  # Red and White
    "DR Congo": {"primary": "#007FFF", "secondary": "#F7D618"},  # Sky Blue and Yellow
    "Belgium": {"primary": "#000000", "secondary": "#FDDA24"},  # Black, Yellow, Red
    "Senegal": {"primary": "#00853F", "secondary": "#FDEF42"},  # Green, Yellow, Red
    "United States": {"primary": "#B22234", "secondary": "#3C3B6E"},  # Red, White, Blue
    "Bosnia & Herzegovina": {"primary": "#002395", "secondary": "#FECB00"},  # Blue and Yellow
    "Spain": {"primary": "#AA151B", "secondary": "#F1BF00"},  # Red and Yellow
    "Austria": {"primary": "#ED2939", "secondary": "#FFFFFF"},  # Red and White
    "Portugal": {"primary": "#006600", "secondary": "#FF0000"},  # Green and Red
    "Croatia": {"primary": "#171796", "secondary": "#FF0000"},  # Blue, White, Red
    "Switzerland": {"primary": "#FF0000", "secondary": "#FFFFFF"},  # Red and White
    "Algeria": {"primary": "#006233", "secondary": "#FFFFFF"},  # Green and White
    "Australia": {"primary": "#00008B", "secondary": "#FFD700"},  # Blue and Gold
    "Egypt": {"primary": "#CE1126", "secondary": "#000000"},  # Red, White, Black
    "Argentina": {"primary": "#74ACDF", "secondary": "#FFFFFF"},  # Light Blue and White
    "Cape Verde": {"primary": "#003893", "secondary": "#F7D116"},  # Blue, White, Red, Yellow
    "Colombia": {"primary": "#FCD116", "secondary": "#003893"},  # Yellow, Blue, Red
    "Ghana": {"primary": "#006B3F", "secondary": "#FCD116"},  # Red, Gold, Green
}

def get_country_gradient(country_name):
    """Get gradient colors for a country's champion display"""
    colors = COUNTRY_COLORS.get(country_name, {"primary": "#FFD700", "secondary": "#FFA500"})
    return colors["primary"], colors["secondary"]
