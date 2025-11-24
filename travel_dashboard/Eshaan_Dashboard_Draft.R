library(leaflet)
library(httr)
library(jsonlite)

# -----------------------------
# WEATHER API
# -----------------------------
api_key <- "W1Kon4mYmcCeG3QD2cQA5UICUe1XLciu"

get_weather_hourly_now <- function(lat, lon, api_key,
                                   units = "imperial",
                                   timesteps = "1h") {
  base_url <- "https://api.tomorrow.io/v4/weather/forecast"
  
  query <- list(
    location  = paste(lat, lon, sep = ","),
    apikey    = api_key,
    units     = units,
    timesteps = timesteps,
    fields    = "temperature,temperatureApparent,humidity,windSpeed,precipitationProbability"
  )
  
  res <- GET(base_url, query = query)
  stop_for_status(res)
  
  dat <- fromJSON(content(res, "text", encoding = "UTF-8"), simplifyVector = FALSE)
  
  if (length(dat$timelines$hourly) == 0) stop("No hourly data returned from Tomorrow.io")
  
  dat$timelines$hourly[[1]]$values
}

# Safe wrapper so a venue popup still renders if API hiccups
safe_weather <- function(lat, lon) {
  tryCatch(
    get_weather_hourly_now(lat, lon, api_key),
    error = function(e) list(
      temperature = NA,
      temperatureApparent = NA,
      humidity = NA,
      windSpeed = NA,
      precipitationProbability = NA
    )
  )
}

# -----------------------------
# VENUE DATA (edit/add here)
# -----------------------------
venues <- data.frame(
  id = c("usc", "ita_dallas", "ita_waco", "lajolla"),
  name = c(
    "David X. Marks Tennis Stadium",
    "ITA Indoors – SMU Styslinger/Altec (Dallas)",
    "ITA Indoors – Baylor Hawkins Indoor (Waco)",
    "La Jolla Beach & Tennis Club"
  ),
  city_state = c(
    "Los Angeles, CA",
    "Dallas, TX",
    "Waco, TX",
    "La Jolla, CA"
  ),
  lat = c(34.02309, 32.83618, 31.54703, 32.85377),
  lon = c(-118.29063, -96.78041, -97.12095, -117.25944),
  
  capacity = c(
    "~1,000 seats",
    "Main host site • indoor courts",
    "Co-host site • indoor courts",
    "1,000+ (club seating/events)"
  ),
  
  travel_from_latc = c(
    "~11 mi (30–45 min bus)",
    "~1,400 mi (flight)",
    "~1,300 mi (flight)",
    "~100–110 mi (bus/van)"
  ),
  tz_diff = c(
    "0 hr (PT)",
    "+2 hr (CT)",
    "+2 hr (CT)",
    "0 hr (PT)"
  ),
  
  climate = c(
    "Urban LA — warm/dry pockets",
    "Indoor venue; Dallas region humid-subtropical",
    "Indoor venue; Waco region humid-subtropical",
    "Coastal SoCal — mild, marine layer possible"
  ),
  
  conditions = c(
    "Often warmer/drier than Westwood; sun + orientation matter for ends.",
    "Neutral indoors; no wind/sun. Building temp/humidity + ball type drive feel.",
    "Neutral indoors; same as Dallas, but court feel may differ slightly by building.",
    "Outdoor by ocean; breeze + heavier air can slow ball slightly."
  ),
  
  nearby = c(
    "USC Village, Exposition Park",
    "Mockingbird Station area, SMU cafes",
    "Campus cafes, riverfront spots",
    "La Jolla Shores, Cove restaurants"
  ),
  
  # Optional short notes (shows only if not NA)
  notes = c(
    "Outdoor hard. Sun can be a factor; court orientation matters.",
    "16-team event. Early rounds split Waco/Dallas; semis/final at SMU.",
    "Co-host site for early rounds only.",
    "Ocean breeze + heavier air possible; courts can play a touch slower."
  ),
  
  logo_url = c(
    "https://commons.wikimedia.org/wiki/Special:FilePath/USC_Trojans_interlocking_logo.png",
    "https://playsightproduction.playsight.com/temp-media/f51484b778334cd0a69e0d21049e6797-crop-6162807cb1714b68b55282efec9514fd.png",
    "https://1000logos.net/wp-content/uploads/2019/10/Baylor-Bears-Logo-2005.png",
    "https://images.sidearmdev.com/crop?url=https%3A%2F%2Fdxbhsrqyrr690.cloudfront.net%2Fsidearm.nextgen.sites%2Fuclabruins.com%2Fimages%2F2023%2F2%2F17%2FLBTC.png&width=120&height=120&type=webp"
  ),
  
  image_url = c(
    "https://images.sidearmdev.com/resize?url=https%3A%2F%2Fdxbhsrqyrr690.cloudfront.net%2Fsidearm.nextgen.sites%2Fusctrojans.com%2Fimages%2F2016%2F4%2F12%2Fm_tennis_auto_original_9298542.jpeg&height=1100&type=webp",
    "https://i.ytimg.com/vi/k_mmgNXIbw4/maxresdefault.jpg?sqp=-oaymwEmCIAKENAF8quKqQMa8AEB-AH-CYAC0AWKAgwIABABGFggZShNMA8=&rs=AOn4CLDr-Z-abqp5IUJiZ5oYYFDbQ2lgqw",
    "https://lh6.googleusercontent.com/proxy/sGrZR0uANmhTUbzqPzwQgYlN8LwKdNkfh57cwL9e8z7K5Sgve1OmUzTh_dzhvu7h4RCdUEvHQZQlGZf-hP6VW0yHvXOXnk4Fy0n4c4pt30Q6D5zVN59O4NI",
    "https://images.trvl-media.com/lodging/1000000/10000/4600/4511/58453bd4.jpg?impolicy=resizecrop&rw=900&rh=500&ra=fill"
  ),
  
  g1 = c("#990000", "#FFB300", "#154734", "#2774AE"),
  g2 = c("#FFC72C", "#2774AE", "#FFB300", "#FFB300"),
  
  stringsAsFactors = FALSE
)

# -----------------------------
# POPUP BUILDER (gradient + accordion dropdowns + weather)
# -----------------------------
make_popup <- function(v) {
  w <- safe_weather(v$lat, v$lon)
  
  temp   <- ifelse(is.na(w$temperature), "—", paste0(round(w$temperature), " °F"))
  feel   <- ifelse(is.na(w$temperatureApparent), "—", paste0(round(w$temperatureApparent), " °F"))
  hum    <- ifelse(is.na(w$humidity), "—", paste0(round(w$humidity), "%"))
  wind   <- ifelse(is.na(w$windSpeed), "—", paste0(round(w$windSpeed), " mph"))
  precip <- ifelse(is.na(w$precipitationProbability), "—", paste0(round(w$precipitationProbability), "%"))
  
  acc_id <- paste0("acc_", v$id)
  radio_name <- paste0("grp_", v$id)
  
  # Optional Notes section
  notes_block <- ""
  if (!is.null(v$notes) && !is.na(v$notes) && nchar(v$notes) > 0) {
    notes_block <- paste0(
      "<div class='acc-item'>",
      "<input class='acc-radio' type='radio' name='", radio_name, "' id='", acc_id, "_notes'>",
      "<label class='acc-label' for='", acc_id, "_notes'>Notes</label>",
      "<div class='acc-panel'>", v$notes, "</div>",
      "</div>"
    )
  }
  
  paste0(
    "<div id='", acc_id, "' style='font-family:system-ui,-apple-system,\"Segoe UI\",sans-serif; width:320px;'>",
    "<div style='border-radius:14px; overflow:hidden; box-shadow:0 6px 18px rgba(0,0,0,0.25); border:1px solid #e6e6e6;'>",
    
    # Header
    "<div style='display:flex; align-items:center; gap:10px; padding:10px; ",
    "background:linear-gradient(135deg,", v$g1, ",", v$g2, ");'>",
    "<img src='", v$logo_url, "' style='width:38px; height:28px; object-fit:contain; background:white; border-radius:7px; padding:3px;'>",
    "<div>",
    "<div style='font-size:15px; font-weight:800; color:#fff; line-height:1.1;'>", v$name, "</div>",
    "<div style='font-size:12px; color:rgba(255,255,255,0.9);'>", v$city_state, "</div>",
    "</div>",
    "</div>",
    
    # Image
    "<img src='", v$image_url, "' style='width:100%; height:160px; object-fit:cover; display:block;'>",
    
    # Body
    "<div style='padding:10px; background:#fff;'>",
    "<div style='font-size:12.5px; color:#222; margin-bottom:8px;'>",
    "<b>Setup:</b> ", v$capacity,
    "</div>",
    
    # Accordion CSS (radio-based, no JS)
    "<style>
            #", acc_id, " .acc-item{
              border-radius:10px; 
              background:#f8f9fb; 
              border:1px solid #ececec; 
              margin-bottom:7px; 
              overflow:hidden;
            }
            #", acc_id, " .acc-radio{
              display:none;
            }
            #", acc_id, " .acc-label{
              cursor:pointer;
              padding:8px 10px;
              font-size:13.5px;
              font-weight:700;
              color:#111;
              display:flex;
              align-items:center;
              justify-content:space-between;
              background:#f8f9fb;
            }
            #", acc_id, " .acc-label:hover{ background:#f1f3f6; }
            #", acc_id, " .acc-label::after{
              content:'▾';
              font-size:14px;
              opacity:0.7;
              transition:transform 0.15s ease;
            }
            #", acc_id, " .acc-panel{
              display:none;
              padding:8px 10px;
              font-size:12.5px;
              color:#333;
              line-height:1.35;
              background:#fff;
            }
            #", acc_id, " .acc-radio:checked + .acc-label{
              background:#eef2f7;
            }
            #", acc_id, " .acc-radio:checked + .acc-label::after{
              transform:rotate(180deg);
            }
            #", acc_id, " .acc-radio:checked + .acc-label + .acc-panel{
              display:block;
            }
            #", acc_id, " .weather-panel{
              background:#f7f7f7;
              border-radius:8px;
            }
          </style>",
    
    # Travel (default open)
    "<div class='acc-item'>",
    "<input class='acc-radio' type='radio' name='", radio_name, "' id='", acc_id, "_travel' checked>",
    "<label class='acc-label' for='", acc_id, "_travel'>Travel</label>",
    "<div class='acc-panel'>",
    v$travel_from_latc, "<br>",
    "<b>Time zone:</b> ", v$tz_diff,
    "</div>",
    "</div>",
    
    # Conditions
    "<div class='acc-item'>",
    "<input class='acc-radio' type='radio' name='", radio_name, "' id='", acc_id, "_cond'>",
    "<label class='acc-label' for='", acc_id, "_cond'>Conditions</label>",
    "<div class='acc-panel'>",
    v$climate, "<br>", v$conditions,
    "</div>",
    "</div>",
    
    # Weather now
    "<div class='acc-item'>",
    "<input class='acc-radio' type='radio' name='", radio_name, "' id='", acc_id, "_weather'>",
    "<label class='acc-label' for='", acc_id, "_weather'>Weather now</label>",
    "<div class='acc-panel weather-panel'>",
    "<div><b>Temp:</b> ", temp, " &nbsp; <b>Feels:</b> ", feel, "</div>",
    "<div><b>Humidity:</b> ", hum, " &nbsp; <b>Wind:</b> ", wind, "</div>",
    "<div><b>Precip chance:</b> ", precip, "</div>",
    "</div>",
    "</div>",
    
    # Nearby
    "<div class='acc-item'>",
    "<input class='acc-radio' type='radio' name='", radio_name, "' id='", acc_id, "_nearby'>",
    "<label class='acc-label' for='", acc_id, "_nearby'>Nearby</label>",
    "<div class='acc-panel'>", v$nearby, "</div>",
    "</div>",
    
    notes_block,
    
    "</div>", # body
    "</div>",   # card
    "</div>"      # root
  )
}

# -----------------------------
# MAP + MARKERS
# -----------------------------
my_map <- leaflet() |>
  addTiles() |>
  setView(lng = -98.35, lat = 39.5, zoom = 4)

for (i in seq_len(nrow(venues))) {
  v <- venues[i, ]
  
  icon <- makeIcon(
    iconUrl = v$logo_url,
    iconWidth = 36,
    iconHeight = 30
  )
  
  my_map <- addMarkers(
    my_map,
    lng = v$lon,
    lat = v$lat,
    icon = icon,
    popup = make_popup(v),
    popupOptions = popupOptions(maxWidth = 420)
  )
}

my_map

