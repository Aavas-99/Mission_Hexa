THEMES = [
    {
        "name": "Golden Hive",
        "background": (24, 27, 34),
        "panel": (38, 44, 55),
        "cell": (232, 178, 48),
        "visited": (75, 80, 85),
        "text": (245, 245, 245),
        "accent": (250, 190, 45),
        "border": (20, 20, 22),
        "legal_move": (70, 210, 125)
    },
    {
        "name": "Forest Hive",
        "background": (18, 35, 29),
        "panel": (32, 55, 47),
        "cell": (95, 165, 100),
        "visited": (65, 78, 70),
        "text": (240, 248, 242),
        "accent": (130, 225, 145),
        "border": (15, 25, 20),
        "legal_move": (100, 230, 155)
    },
    {
        "name": "Royal Hive",
        "background": (31, 22, 43),
        "panel": (53, 39, 68),
        "cell": (168, 112, 210),
        "visited": (79, 70, 90),
        "text": (248, 242, 252),
        "accent": (225, 170, 255),
        "border": (20, 15, 28),
        "legal_move": (90, 215, 190)
    }
]


def get_theme(theme_index):
    return THEMES[theme_index]