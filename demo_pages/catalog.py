"""Product catalogs used by the comparison demo pages.

Kept separate from the BM25 page's SHOP_PRODUCTS so each page's results stay
stable when another page's data is edited.
"""

# (sku, title, description, category, price)
# Used by the Hybrid and Vector Range pages. Includes near-duplicate listings
# (same product from different sellers) for the range "find duplicates" demo.
CATALOG = [
    (1001, "Noise Cancelling Headphones", "Over-ear wireless headphones with active noise cancelling and 30-hour battery.", "electronics", 249),
    (1002, "ANC Travel Earbuds", "Compact earbuds that block engine hum on flights and trains. Includes charging case.", "electronics", 129),
    (1003, "Studio Monitor Headphones", "Wired closed-back headphones with flat response for mixing and recording.", "electronics", 159),
    (1004, "Bluetooth Party Speaker", "Loud portable speaker with bass boost and light show.", "electronics", 99),
    (1005, "Kids Volume-Limited Headphones", "Durable on-ear headphones capped at 85 dB to protect young ears.", "electronics", 29),
    (1006, "Foam Ear Plugs (50 pairs)", "Soft disposable ear plugs for sleeping, studying and loud concerts.", "personal care", 9),
    (1007, "White Noise Sleep Machine", "Plays fan, rain and ocean sounds to mask snoring and street noise.", "home", 45),
    (1010, "Insulated Travel Mug", "Double-wall vacuum mug keeps coffee hot for 8 hours. Leak-proof lid.", "kitchen", 28),
    (1011, "Stainless Steel Water Bottle 750ml", "Vacuum insulated bottle keeps water cold for 24 hours.", "kitchen", 32),
    (1012, "Insulated Stainless Water Bottle - 750 ml", "Double-wall vacuum insulated steel bottle, keeps drinks cold 24 hours.", "kitchen", 30),
    (1013, "Vacuum Insulated Steel Bottle 0.75L", "Keeps beverages ice cold for a full day. Stainless steel, BPA free.", "kitchen", 27),
    (1014, "Burr Coffee Grinder", "Conical burr grinder with 18 grind settings for espresso to French press.", "kitchen", 89),
    (1015, "Pour-Over Coffee Kettle", "Gooseneck kettle with built-in thermometer for precise brewing.", "kitchen", 55),
    (1016, "Electric Lunch Box", "Plug-in lunch box that warms your meal at the office in 30 minutes.", "kitchen", 39),
    (1020, "XR-200 Trail Running Shoes", "Grippy trail shoes with rock plate for technical mountain paths.", "shoes", 139),
    (1021, "Road Running Shoes", "Lightweight cushioned shoes for daily road miles.", "shoes", 119),
    (1022, "Waterproof Hiking Boots", "Leather boots with sealed membrane that keep feet dry on wet trails.", "shoes", 179),
    (1023, "Barefoot Minimalist Sneakers", "Zero-drop flexible sneakers with a thin sole for natural movement.", "shoes", 95),
    (1024, "Leather Office Loafers", "Classic slip-on loafers for business casual.", "shoes", 129),
    (1030, "Packable Rain Jacket", "Lightweight waterproof shell with sealed seams that folds into its pocket.", "apparel", 89),
    (1031, "Merino Wool Base Layer", "Breathable thermal top that regulates temperature and resists odor.", "apparel", 75),
    (1032, "Reflective Running Vest", "High-visibility vest so drivers can see you on early morning runs.", "apparel", 25),
    (1033, "Down Puffer Jacket", "Warm insulated jacket for freezing winter days.", "apparel", 199),
    (1040, "GPS Running Watch", "Tracks pace, distance and heart rate on every run.", "electronics", 199),
    (1041, "Chest Heart Rate Strap", "Accurate ECG-grade heart rate monitor for training zones.", "electronics", 69),
    (1042, "Smart Body Scale", "Measures weight, body fat and muscle mass and syncs to your phone.", "electronics", 59),
    (1050, "Foam Roller", "Firm roller for muscle recovery and myofascial release after workouts.", "fitness", 30),
    (1051, "Adjustable Dumbbells", "Pair of dumbbells that adjust from 5 to 52 lbs with a dial.", "fitness", 299),
    (1052, "Yoga Mat", "Non-slip extra thick mat for yoga and pilates.", "fitness", 40),
    (1053, "Resistance Bands Set", "Five latex bands with handles for strength training at home.", "fitness", 25),
    (1060, "Two-Person Camping Tent", "Freestanding tent that sets up in five minutes.", "outdoor", 210),
    (1061, "Headlamp 400 Lumen", "Rechargeable head torch for night hikes and camping.", "outdoor", 35),
    (1062, "Hydration Backpack", "Running pack with a 2-liter water bladder and phone pocket.", "outdoor", 79),
    (1063, "Portable Camp Stove", "Compact gas stove that boils water in three minutes.", "outdoor", 49),
    (1070, "Ergonomic Office Chair", "Mesh chair with lumbar support for long work days.", "furniture", 349),
    (1071, "Standing Desk Converter", "Sit-stand riser that turns any desk into a standing desk.", "furniture", 189),
    (1072, "Laptop Stand", "Aluminum stand that raises your screen to eye level.", "furniture", 45),
    # Keyword traps: accessories whose text repeats a shopper's words but that are not
    # what the shopper is looking for. Real catalogs are full of these, and they are
    # what makes keyword-only and semantic-only rankings disagree.
    (1080, "Carrying Case for Noise Cancelling Headphones",
     "Hard shell case that protects noise cancelling headphones and their cables.", "accessories", 19),
    (1081, "Replacement Ear Cushions for Headphones",
     "Memory foam ear pads for over-ear noise cancelling headphones.", "accessories", 15),
    (1082, "Rain Jacket Repair Patches",
     "Waterproof self-adhesive patches to fix tears in a rain jacket.", "accessories", 9),
    (1083, "Coffee Mug Coasters (set of 4)", "Cork coasters for your coffee mug and hot drinks.", "kitchen", 12),
]

# Localized storefront for the Multi-language page: the same products, written in
# each store's language. (sku, title, description, category, price)
# sku 13 is a keyword-stuffed marketplace listing; BM25 should rank it below the
# focused listings. Example queries in multilang.py were checked against this
# data; re-check them if you edit it.
STORE = {
    "english": [
        (1, "Lightweight Running Shoes", "Breathable running shoes with soft cushioning for daily runs.", "shoes", 89),
        (2, "Trail Running Shoes", "Grippy shoes for muddy and rocky mountain trails.", "shoes", 119),
        (3, "Waterproof Running Jacket", "Light jacket that keeps runners dry in the rain.", "apparel", 99),
        (4, "Insulated Water Bottle", "Steel bottle that keeps drinks cold for 24 hours.", "accessories", 29),
        (5, "Hiking Backpack 30L", "Comfortable backpack with a rain cover for day hikes.", "accessories", 79),
        (6, "Running Socks (3 pairs)", "Cushioned socks that prevent blisters on long runs.", "apparel", 19),
        (7, "GPS Running Watch", "Tracks your pace, distance and heart rate.", "electronics", 199),
        (8, "Wireless Sport Earbuds", "Sweat-resistant earbuds that stay in while you run.", "electronics", 69),
        (9, "Yoga Mat", "Non-slip mat for yoga and stretching.", "accessories", 35),
        (10, "Kids Rain Jacket", "Colorful waterproof jacket for children.", "apparel", 45),
        (11, "Thermal Running Tights", "Warm tights for running in winter.", "apparel", 59),
        (12, "Rechargeable Headlamp", "Bright head torch for running and hiking in the dark.", "electronics", 39),
        (13, "Running Shoes Sneakers Trainers Cheap Sale Men Women Kids",
         "running shoes running sneakers running trainers best price free shipping new arrival hot deal "
         "top rated all sizes all colors gym walking jogging marathon fitness gift idea", "shoes", 25),
    ],
    "german": [
        (1, "Leichte Laufschuhe", "Atmungsaktive Laufschuhe mit weicher Dämpfung für tägliche Läufe.", "Schuhe", 89),
        (2, "Trail-Laufschuhe", "Griffige Schuhe für schlammige und felsige Bergpfade.", "Schuhe", 119),
        (3, "Wasserdichte Laufjacke", "Leichte Jacke, die Läufer im Regen trocken hält.", "Bekleidung", 99),
        (4, "Isolierte Trinkflasche", "Flasche aus Stahl, die Getränke 24 Stunden kalt hält.", "Zubehör", 29),
        (5, "Wanderrucksack 30 L", "Bequemer Rucksack mit Regenhülle für Tageswanderungen.", "Zubehör", 79),
        (6, "Laufsocken (3 Paar)", "Gepolsterte Socken gegen Blasen auf langen Läufen.", "Bekleidung", 19),
        (7, "GPS-Laufuhr", "Misst Tempo, Distanz und Herzfrequenz.", "Elektronik", 199),
        (8, "Kabellose Sport-Kopfhörer", "Schweißresistente Kopfhörer, die beim Laufen halten.", "Elektronik", 69),
        (9, "Yogamatte", "Rutschfeste Matte für Yoga und Dehnübungen.", "Zubehör", 35),
        (10, "Regenjacke für Kinder", "Bunte, wasserdichte Jacke für Kinder.", "Bekleidung", 45),
        (11, "Thermo-Lauftights", "Warme Tights zum Laufen im Winter.", "Bekleidung", 59),
        (12, "Aufladbare Stirnlampe", "Helle Lampe zum Laufen und Wandern im Dunkeln.", "Elektronik", 39),
        (13, "Laufschuhe Sneaker Turnschuhe günstig Sale Herren Damen Kinder",
         "Laufschuhe Laufschuhe Sneaker Turnschuhe bester Preis kostenloser Versand neu Angebot Bestseller "
         "alle Größen alle Farben Fitness Joggen Marathon Training Geschenkidee", "Schuhe", 25),
    ],
    "spanish": [
        (1, "Zapatillas de running ligeras", "Zapatillas transpirables con amortiguación suave para correr a diario.", "Calzado", 89),
        (2, "Zapatillas de trail", "Zapatillas con buen agarre para senderos de montaña con barro y rocas.", "Calzado", 119),
        (3, "Chaqueta impermeable para correr", "Chaqueta ligera que mantiene secos a los corredores bajo la lluvia.", "Ropa", 99),
        (4, "Botella térmica", "Botella de acero que mantiene las bebidas frías durante 24 horas.", "Accesorios", 29),
        (5, "Mochila de senderismo 30 L", "Mochila cómoda con funda para la lluvia, para excursiones de un día.", "Accesorios", 79),
        (6, "Calcetines de running (3 pares)", "¡Calcetines acolchados que evitan ampollas en carreras largas!", "Ropa", 19),
        (7, "Reloj GPS para correr", "Mide el ritmo, la distancia y la frecuencia cardíaca.", "Electrónica", 199),
        (8, "Auriculares deportivos inalámbricos", "Auriculares resistentes al sudor que no se caen al correr.", "Electrónica", 69),
        (9, "Esterilla de yoga", "Esterilla antideslizante para yoga y estiramientos.", "Accesorios", 35),
        (10, "Chubasquero infantil", "¿Llueve? Chaqueta impermeable de colores para niños.", "Ropa", 45),
        (11, "Mallas térmicas de running", "Mallas cálidas para correr en invierno.", "Ropa", 59),
        (12, "Linterna frontal recargable", "Linterna potente para correr y hacer senderismo de noche.", "Electrónica", 39),
        (13, "Zapatillas deportivas baratas oferta hombre mujer niños",
         "zapatillas zapatillas zapatillas running mejor precio envío gratis novedad oferta más vendidas "
         "todas las tallas todos los colores gimnasio maratón fitness idea regalo", "Calzado", 25),
    ],
    "french": [
        (1, "Chaussures de course légères", "Chaussures respirantes avec un amorti souple pour courir tous les jours.", "Chaussures", 89),
        (2, "Chaussures de trail", "Chaussures accrocheuses pour les sentiers de montagne boueux et rocheux.", "Chaussures", 119),
        (3, "Veste de course imperméable", "Veste légère qui garde les coureurs au sec sous la pluie.", "Vêtements", 99),
        (4, "Gourde isotherme", "Gourde en acier qui garde les boissons fraîches pendant 24 heures.", "Accessoires", 29),
        (5, "Sac à dos de randonnée 30 L", "Sac à dos confortable avec housse de pluie pour les randonnées à la journée.", "Accessoires", 79),
        (6, "Chaussettes de course (3 paires)", "Chaussettes rembourrées contre les ampoules sur les longues sorties.", "Vêtements", 19),
        (7, "Montre GPS de course", "Mesure l'allure, la distance et la fréquence cardiaque.", "Électronique", 199),
        (8, "Écouteurs sport sans fil", "Écouteurs résistants à la transpiration qui tiennent pendant la course.", "Électronique", 69),
        (9, "Tapis de yoga", "Tapis antidérapant pour le yoga et les étirements.", "Accessoires", 35),
        (10, "Veste de pluie pour enfants", "Veste imperméable et colorée pour les enfants.", "Vêtements", 45),
        (11, "Collant thermique de course", "Collant chaud pour courir en hiver.", "Vêtements", 59),
        (12, "Lampe frontale rechargeable", "Lampe puissante pour courir et randonner dans le noir.", "Électronique", 39),
        (13, "Chaussures baskets pas cher promo homme femme enfant",
         "chaussures chaussures chaussures course meilleur prix livraison gratuite nouveauté promo meilleures "
         "ventes toutes tailles toutes couleurs gym marathon fitness idée cadeau", "Chaussures", 25),
    ],
}


# BM25 scoring page catalog, by Miles Song (from the original BM25 page).
# (title, description, category, price)
# Tuned so each step shows its effect: e.g. the keyword-stuffed listing (#3) must
# lose to the focused one on "running shoes", and the waterproof shoes must rank
# last on plain "shoes" so the boost visibly lifts them. Descriptions say "running",
# not "run": "run" is indexed as a separate, rarer term and skews scores. Re-check if you edit.
SHOP_PRODUCTS = [
    ("Running Shoes", "Lightweight running shoes for everyday running.", "shoes", 45),
    ("Trail Running Shoes", "Grippy trail running shoes built for rocky mountain paths.", "shoes", 95),
    ("Running Shoes Sneakers Trainers - Men Women Kids - Best Cheap Sale",
     "running shoes running sneakers running trainers jogging shoes walking shoes gym shoes tennis shoes "
     "sports shoes casual shoes marathon running shoes best running shoes cheap shoes discount shoes "
     "sale shoes free shipping new arrival hot deal top rated shoes buy now limited offer men women kids all "
     "sizes all colors great for gym workouts walking travel school office weekend parties summer winter "
     "spring autumn style comfort value quality guaranteed fast delivery easy returns gift idea", "shoes", 29),
    ("Waterproof Hiking Shoes",
     "Sturdy waterproof hiking shoes with a sealed membrane, ankle support and a deep lug outsole "
     "for wet, muddy trails.", "shoes", 120),
    ("Rain-Ready Trail Shoes",
     "Waterproof trail shoes with a breathable lining that keep your feet dry through puddles "
     "and heavy rain.", "shoes", 110),
    ("Leather Dress Shoes", "Classic leather dress shoes for the office.", "shoes", 150),
    ("Canvas Slip-On Shoes", "Casual canvas shoes for everyday wear.", "shoes", 39),
    ("Waterproof Rain Jacket", "Packable waterproof jacket with sealed seams.", "apparel", 80),
    ("Running Jacket", "Windproof jacket for running in cold weather.", "apparel", 70),
    ("Down Jacket", "Warm insulated down jacket for winter.", "apparel", 160),
    ("Running Socks (3-Pack)", "Cushioned moisture-wicking socks for running.", "apparel", 15),
    ("Running Shorts", "Breathable running shorts with a zip pocket.", "apparel", 30),
    ("GPS Running Watch", "Tracks pace, distance and heart rate on every workout.", "electronics", 199),
    ("Wireless Earbuds", "Sweat-resistant earbuds that stay put during workouts.", "electronics", 89),
    ("Insulated Water Bottle", "Keeps drinks cold for 24 hours.", "kitchen", 25),
    ("Yoga Mat", "Non-slip mat for yoga and pilates.", "fitness", 40),
    ("Foam Roller", "Firm foam roller for stretching and muscle recovery after running or the gym.",
     "fitness", 30),
    ("Hiking Backpack", "Lightweight backpack with padded straps.", "outdoor", 85),
    ("Camping Tent", "Two-person tent for weekend trips.", "outdoor", 210),
    ("Wool Beanie", "Soft knit beanie for cold mornings.", "apparel", 20),
]
