library(leaflet)

# Base map ----------------------------------------------------------
my_map <- leaflet() |>
  addTiles() |>
  setView(lng = -98.35, lat = 39.5, zoom = 4)

# Logo URLs (via Special:FilePath so they resolve to actual images) ----
USC_logo_url <- "https://commons.wikimedia.org/wiki/Special:FilePath/USC_Trojans_interlocking_logo.png"
ITA_logo_url <- "https://commons.wikimedia.org/wiki/Special:FilePath/ITA_New_Logo.png"

# Court images (your links) -----------------------------------------
USC_image <- "https://images.sidearmdev.com/resize?url=https%3A%2F%2Fdxbhsrqyrr690.cloudfront.net%2Fsidearm.nextgen.sites%2Fusctrojans.com%2Fimages%2F2016%2F4%2F12%2Fm_tennis_auto_original_9298542.jpeg&height=1100&type=webp"

ITA_image <- "https://i.ytimg.com/vi/k_mmgNXIbw4/maxresdefault.jpg?sqp=-oaymwEmCIAKENAF8quKqQMa8AEB-AH-CYAC0AWKAgwIABABGFggZShNMA8=&rs=AOn4CLDr-Z-abqp5IUJiZ5oYYFDbQ2lgqw"

# Icons for map markers ---------------------------------------------
USC_icon <- makeIcon(
  iconUrl   = USC_logo_url,
  iconWidth = 35,
  iconHeight = 35
)

ITA_icon <- makeIcon(
  iconUrl   = ITA_logo_url,
  iconWidth = 35,
  iconHeight = 30
)

# ---------------- USC (Los Angeles Away) ---------------------------

USC_popup <- paste0(
  "<div style='font-family:system-ui,-apple-system,\"Segoe UI\",sans-serif; width:280px;'>",
  "<div style='border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.25); border:1px solid #dddddd;'>",
  
  # Header with logo + title
  "<div style='display:flex; align-items:center; gap:8px; padding:6px 8px; ",
  "background:linear-gradient(135deg,#990000,#FFC72C);'>",
  "<img src='", USC_logo_url, "' ",
  "style='width:32px; height:32px; object-fit:contain; background:#ffffff; ",
  "border-radius:6px; padding:2px;'>",
  "<div>",
  "<div style='font-size:13px; font-weight:700; color:#ffffff;'>David X. Marks Tennis Stadium</div>",
  "<div style='font-size:11px; color:#FFEFD5;'>Los Angeles, CA • 34.0231° N, 118.2906° W</div>",
  "</div>",
  "</div>",
  
  # Image
  "<img src='", USC_image, "' ",
  "style='width:100%; height:130px; object-fit:cover; display:block;'>",
  
  # Body
  "<div style='padding:8px 10px; background:#ffffff;'>",
  
  "<div style='font-size:12px; color:#222; margin-bottom:4px;'>",
  "<b>Setup:</b> Outdoor hard court • ~1,000 seats.",
  "</div>",
  
  "<div style='font-size:12px; color:#222; margin-bottom:4px;'>",
  "<b>Travel from LATC:</b> ~11 miles across LA (about 30–45 min by bus) • same time zone (PT).",
  "</div>",
  
  "<div style='font-size:12px; color:#222; margin-bottom:4px;'>",
  "<b>Conditions:</b> Often slightly warmer and drier than Westwood. ",
  "Sun angle and court orientation can influence preferred ends.",
  "</div>",
  
  "<div style='font-size:12px; color:#222;'>",
  "<b>Nearby:</b> USC Village and Exposition Park area for quick food and post-match recovery.",
  "</div>",
  
  "</div>",
  "</div>",
  "</div>"
)

my_map <- addMarkers(
  my_map,
  lng   = -118.29063,   # David X. Marks Tennis Stadium
  lat   = 34.02309,
  icon  = USC_icon,
  popup = USC_popup,
  popupOptions = popupOptions(maxWidth = 380)
)

# -------- ITA National Indoors (Dallas / Waco, TX) -----------------

ITA_popup <- paste0(
  "<div style='font-family:system-ui,-apple-system,\"Segoe UI\",sans-serif; width:280px;'>",
  "<div style='border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.25); border:1px solid #dddddd;'>",
  
  # Header with logo + title
  "<div style='display:flex; align-items:center; gap:8px; padding:6px 8px; ",
  "background:linear-gradient(135deg,#FFB300,#2774AE);'>",
  "<img src='", ITA_logo_url, "' ",
  "style='width:34px; height:26px; object-fit:contain; background:#ffffff; ",
  "border-radius:6px; padding:2px;'>",
  "<div>",
  "<div style='font-size:13px; font-weight:800; color:#1b1b1b;'>ITA National Team Indoors</div>",
  "<div style='font-size:11px; color:#333333;'>Dallas & Waco, TX (SMU & Baylor)</div>",
  "</div>",
  "</div>",
  
  # Image
  "<img src='", ITA_image, "' ",
  "style='width:100%; height:130px; object-fit:cover; display:block;'>",
  
  # Body
  "<div style='padding:8px 10px; background:#ffffff;'>",
  
  "<div style='font-size:12px; color:#222; margin-bottom:4px;'>",
  "<b>Setup:</b> Indoor hard courts at SMU's Styslinger/Altec (Dallas) and Baylor's Hawkins Indoor (Waco).",
  "</div>",
  
  "<div style='font-size:12px; color:#222; margin-bottom:4px;'>",
  "<b>Format:</b> 16-team D1 field. Early rounds split between Waco and Dallas; ",
  "semifinals and final at SMU in Dallas.",
  "</div>",
  
  "<div style='font-size:12px; color:#222; margin-bottom:4px;'>",
  "<b>Travel from LATC:</b> About 1,400 miles (flight plus local transit) • +2 hours time zone (Central).",
  "</div>",
  
  "<div style='font-size:12px; color:#222; margin-bottom:4px;'>",
  "<b>Conditions:</b> Neutral indoor environment – no sun or wind. ",
  "Match feel depends on building temperature, humidity, and ball type.",
  "</div>",
  
  "<div style='font-size:12px; color:#222;'>",
  "<b>Nearby:</b> Dallas – SMU/Mockingbird Station area. ",
  "Waco – campus cafés and riverfront spots suitable for team meals and recovery.",
  "</div>",
  
  "</div>",
  "</div>",
  "</div>"
)

my_map <- addMarkers(
  my_map,
  lng   = -96.78041,   # Styslinger/Altec Tennis Complex (Dallas host site)
  lat   = 32.83618,
  icon  = ITA_icon,
  popup = ITA_popup,
  popupOptions = popupOptions(maxWidth = 380)
)

# View the map -------------------------------------------------------
my_map
