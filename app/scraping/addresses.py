"""
Representative Addresses - 30 delivery addresses across 8 Mexican cities.

Each address has approximate real coordinates and a zone_type classification
(premium/middle/popular) to analyze competitiveness by segment.
"""

ADDRESSES = [
    # --- CDMX (8) ---
    {"id": "cdmx_polanco", "label": "Polanco, CDMX", "address": "Av. Presidente Masaryk 260, Polanco, Miguel Hidalgo, CDMX", "latitude": 19.4333, "longitude": -99.1907, "zone_type": "premium", "city": "CDMX"},
    {"id": "cdmx_condesa", "label": "Condesa, CDMX", "address": "Av. Tamaulipas 90, Condesa, Cuauhtemoc, CDMX", "latitude": 19.4116, "longitude": -99.1741, "zone_type": "premium", "city": "CDMX"},
    {"id": "cdmx_roma", "label": "Roma Norte, CDMX", "address": "Calle Orizaba 101, Roma Norte, Cuauhtemoc, CDMX", "latitude": 19.4178, "longitude": -99.1630, "zone_type": "premium", "city": "CDMX"},
    {"id": "cdmx_santafe", "label": "Santa Fe, CDMX", "address": "Av. Vasco de Quiroga 3800, Santa Fe, Alvaro Obregon, CDMX", "latitude": 19.3660, "longitude": -99.2615, "zone_type": "premium", "city": "CDMX"},
    {"id": "cdmx_coyoacan", "label": "Coyoacan, CDMX", "address": "Calle Francisco Sosa 383, Coyoacan, CDMX", "latitude": 19.3467, "longitude": -99.1617, "zone_type": "middle", "city": "CDMX"},
    {"id": "cdmx_tlalpan", "label": "Tlalpan, CDMX", "address": "Calzada de Tlalpan 1500, Tlalpan, CDMX", "latitude": 19.2944, "longitude": -99.1553, "zone_type": "middle", "city": "CDMX"},
    {"id": "cdmx_iztapalapa", "label": "Iztapalapa, CDMX", "address": "Av. Ermita Iztapalapa 3100, Iztapalapa, CDMX", "latitude": 19.3580, "longitude": -99.0907, "zone_type": "popular", "city": "CDMX"},
    {"id": "cdmx_xochimilco", "label": "Xochimilco, CDMX", "address": "Av. Guadalupe I. Ramirez 505, Xochimilco, CDMX", "latitude": 19.2619, "longitude": -99.1025, "zone_type": "popular", "city": "CDMX"},
    # --- Guadalajara (4) ---
    {"id": "gdl_providencia", "label": "Providencia, Guadalajara", "address": "Av. Providencia 2577, Providencia, Guadalajara, Jalisco", "latitude": 20.6936, "longitude": -103.3917, "zone_type": "premium", "city": "Guadalajara"},
    {"id": "gdl_chapultepec", "label": "Chapultepec, Guadalajara", "address": "Av. Chapultepec 310, Americana, Guadalajara, Jalisco", "latitude": 20.6764, "longitude": -103.3657, "zone_type": "premium", "city": "Guadalajara"},
    {"id": "gdl_zapopan", "label": "Zapopan Centro, Guadalajara", "address": "Av. Hidalgo 100, Centro, Zapopan, Jalisco", "latitude": 20.7211, "longitude": -103.3918, "zone_type": "middle", "city": "Guadalajara"},
    {"id": "gdl_tlaquepaque", "label": "Tlaquepaque, Guadalajara", "address": "Calle Independencia 208, Tlaquepaque, Jalisco", "latitude": 20.6408, "longitude": -103.3127, "zone_type": "popular", "city": "Guadalajara"},
    # --- Monterrey (4) ---
    {"id": "mty_sanpedro", "label": "San Pedro, Monterrey", "address": "Calzada del Valle 400, San Pedro Garza Garcia, NL", "latitude": 25.6535, "longitude": -100.3384, "zone_type": "premium", "city": "Monterrey"},
    {"id": "mty_valle", "label": "Valle, Monterrey", "address": "Av. Eugenio Garza Sada 2501, Valle, Monterrey, NL", "latitude": 25.6318, "longitude": -100.2895, "zone_type": "middle", "city": "Monterrey"},
    {"id": "mty_centro", "label": "Centro, Monterrey", "address": "Calle Morelos 530, Centro, Monterrey, NL", "latitude": 25.6711, "longitude": -100.3100, "zone_type": "middle", "city": "Monterrey"},
    {"id": "mty_cumbres", "label": "Cumbres, Monterrey", "address": "Av. Paseo de los Leones 2100, Cumbres, Monterrey, NL", "latitude": 25.7356, "longitude": -100.3670, "zone_type": "middle", "city": "Monterrey"},
    # --- Cancun (3) ---
    {"id": "can_hotelera", "label": "Zona Hotelera, Cancun", "address": "Blvd. Kukulcan km 12.5, Zona Hotelera, Cancun, QR", "latitude": 21.1319, "longitude": -86.7504, "zone_type": "premium", "city": "Cancun"},
    {"id": "can_centro", "label": "Centro, Cancun", "address": "Av. Tulum 26, Centro, Cancun, QR", "latitude": 21.1619, "longitude": -86.8269, "zone_type": "middle", "city": "Cancun"},
    {"id": "can_juarez", "label": "Puerto Juarez, Cancun", "address": "Av. Lopez Portillo 130, Puerto Juarez, Cancun, QR", "latitude": 21.1867, "longitude": -86.8172, "zone_type": "popular", "city": "Cancun"},
    # --- Puebla (3) ---
    {"id": "pue_centro", "label": "Centro, Puebla", "address": "Calle 5 de Mayo 208, Centro, Puebla, Puebla", "latitude": 19.0431, "longitude": -98.1981, "zone_type": "middle", "city": "Puebla"},
    {"id": "pue_angelopolis", "label": "Angelopolis, Puebla", "address": "Blvd. del Nino Poblano 2510, Angelopolis, Puebla", "latitude": 19.0150, "longitude": -98.2425, "zone_type": "premium", "city": "Puebla"},
    {"id": "pue_cholula", "label": "Cholula, Puebla", "address": "Calle 4 Poniente 104, San Pedro Cholula, Puebla", "latitude": 19.0633, "longitude": -98.3028, "zone_type": "middle", "city": "Puebla"},
    # --- Merida (3) ---
    {"id": "mer_centro", "label": "Centro, Merida", "address": "Calle 60 500, Centro, Merida, Yucatan", "latitude": 20.9674, "longitude": -89.6237, "zone_type": "middle", "city": "Merida"},
    {"id": "mer_altabrisa", "label": "Altabrisa, Merida", "address": "Calle 7 315, Altabrisa, Merida, Yucatan", "latitude": 21.0100, "longitude": -89.5958, "zone_type": "premium", "city": "Merida"},
    {"id": "mer_montejo", "label": "Paseo Montejo, Merida", "address": "Paseo de Montejo 480, Merida, Yucatan", "latitude": 20.9836, "longitude": -89.6155, "zone_type": "premium", "city": "Merida"},
    # --- Tijuana (3) ---
    {"id": "tij_zonario", "label": "Zona Rio, Tijuana", "address": "Blvd. Paseo de los Heroes 9211, Zona Rio, Tijuana, BC", "latitude": 32.5277, "longitude": -117.0237, "zone_type": "premium", "city": "Tijuana"},
    {"id": "tij_playas", "label": "Playas, Tijuana", "address": "Av. del Pacifico 300, Playas de Tijuana, BC", "latitude": 32.5186, "longitude": -117.1097, "zone_type": "middle", "city": "Tijuana"},
    {"id": "tij_centro", "label": "Centro, Tijuana", "address": "Av. Revolucion 1000, Centro, Tijuana, BC", "latitude": 32.5318, "longitude": -117.0382, "zone_type": "popular", "city": "Tijuana"},
    # --- Queretaro (2) ---
    {"id": "qro_centro", "label": "Centro, Queretaro", "address": "Calle 5 de Mayo 39, Centro, Queretaro", "latitude": 20.5881, "longitude": -100.3918, "zone_type": "middle", "city": "Queretaro"},
    {"id": "qro_juriquilla", "label": "Juriquilla, Queretaro", "address": "Blvd. Juriquilla 1000, Juriquilla, Queretaro", "latitude": 20.7089, "longitude": -100.4472, "zone_type": "premium", "city": "Queretaro"},
]

REFERENCE_PRODUCTS = [
    {"name": "Big Mac", "category": "fast_food", "restaurant": "McDonalds"},
    {"name": "Combo Mediano McDonalds", "category": "fast_food", "restaurant": "McDonalds"},
    {"name": "McNuggets 10 piezas", "category": "fast_food", "restaurant": "McDonalds"},
    {"name": "Coca-Cola 500ml", "category": "retail", "store": "convenience"},
    {"name": "Agua Natural 1L", "category": "retail", "store": "convenience"},
]
