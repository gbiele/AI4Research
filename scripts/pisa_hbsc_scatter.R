#!/usr/bin/env Rscript
# PISA 2022 (Zenodo DOI 10.5281/zenodo.13382904) vs HBSC composite.
#
# HBSC (default): public data-browser CSVs (prompt):
#   https://data-browser.hbsc.org/wp-content/uploads/csvs/data.csv
#   https://data-browser.hbsc.org/wp-content/uploads/csvs/metadata.csv
# For 15-year-olds, survey year 2022, measures: WHO-5 mean (who5_high), life satisfaction
# (lifesat_mean), self-efficacy problem-solving and goal achievement (d_selfeff_sol,
# d_selfeff_do). Country-level rows are z-scored across countries and averaged (equal weight).
# Optional: WHO Data Warehouse API, HBSC .sav microdata, or a precomputed HBSC CSV — see HBSC_SOURCE.
#
# Optional env vars:
#   PISA_CACHE_DIR, PISA_SKIP_DOWNLOAD, PISA_DOWNLOAD_TIMEOUT_SEC, PISA_MAX_ROWS
#   HBSC_SOURCE          - browser_csv (default), who_dw, sav, or csv
#   HBSC_BROWSER_DATA_URL, HBSC_BROWSER_META_URL, HBSC_BROWSER_DATA_PATH, HBSC_BROWSER_META_PATH
#   HBSC_BROWSER_YEAR, HBSC_BROWSER_AGE  (default 2022 and 15-year-olds)
#   WHO_DW_BASE          - default https://dw.euro.who.int
#   HBSC_DW_MEASURES     - comma-separated measure codes (default HBSC_15,HBSC_16,HBSC_42)
#   HBSC_DW_SIGN         - comma-separated +1 or -1 per measure (default 1,-1,1)
#   HBSC_DW_YEAR         - survey year filter (default 2018)
#   HBSC_DW_AGE          - AGE_GRP_2 dimension (default 15YO; aligns with PISA age)
#   HBSC_DW_SLEEP_SEC    - pause between API calls (default 2) to reduce 429 errors
#   HBSC_INTERNATIONAL_SAV, HBSC_COMPOSITE_CSV — when HBSC_SOURCE is sav / csv
#   PISA_USE_GRADE8  - 0 (default) all 15-year-old sample; 1 = restrict to grade 8 (ST001Q01TA)
#   PISA_GRADE8_CODES - optional comma list of raw numeric grade codes to treat as grade 8
#   OUT_PNG

suppressPackageStartupMessages({
  if (!requireNamespace("dplyr", quietly = TRUE)) stop("install.packages('dplyr')")
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("install.packages('ggplot2')")
  if (!requireNamespace("haven", quietly = TRUE)) stop("install.packages('haven')")
  if (!requireNamespace("tidyr", quietly = TRUE)) stop("install.packages('tidyr')")
  if (!requireNamespace("jsonlite", quietly = TRUE)) stop("install.packages('jsonlite')")
})

zenodo_stu_url <-
  "https://zenodo.org/api/records/13382904/files/CY08MSP_STU_QQQ.sav/content"
pisa_filename <- "CY08MSP_STU_QQQ.sav"

cache_dir <- Sys.getenv("PISA_CACHE_DIR", unset = file.path("data", "cache"))
out_png <- Sys.getenv("OUT_PNG", unset = file.path("figures", "pisa_hbsc_composite_scatter.png"))

dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(out_png), recursive = TRUE, showWarnings = FALSE)

# Geographic Europe (ISO 3166-1 alpha-3) — broad definition; intersect with data.
# Includes PISA subnational codes used in CY08 (UK nations, Kosovo).
europe_iso3 <- c(
  "ALB", "AND", "AUT", "BLR", "BEL", "BIH", "BGR", "HRV", "CYP", "CZE",
  "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ITA",
  "XKX", "LVA", "LIE", "LTU", "LUX", "MLT", "MDA", "MCO", "MNE", "NLD",
  "MKD", "NOR", "POL", "PRT", "ROU", "RUS", "SMR", "SRB", "SVK", "SVN",
  "ESP", "SWE", "CHE", "UKR", "GBR", "VAT", "ARM", "AZE", "GEO", "KAZ",
  "TUR", "ISR", "ENG", "SCT", "WLS", "NIR", "GRL"
)

first_present <- function(nms, candidates) {
  hit <- candidates[candidates %in% nms]
  if (length(hit)) hit[[1]] else NA_character_
}

# Grade-8 filter for PISA 2022 (ST001Q01TA / value labels) — set PISA_GRADE8_CODES if needed.
pisa_is_grade8 <- function(grade_v) {
  s <- Sys.getenv("PISA_GRADE8_CODES", unset = "")
  n <- as.numeric(haven::zap_labels(grade_v))
  if (nzchar(s)) {
    codes <- as.integer(trimws(strsplit(s, ",", fixed = TRUE)[[1]]))
    codes <- codes[is.finite(codes)]
    if (!length(codes)) {
      stop("PISA_GRADE8_CODES is empty or invalid.")
    }
    return(is.finite(n) & n %in% codes)
  }
  if (any(is.finite(n) & n == 8, na.rm = TRUE) && mean(n == 8, na.rm = TRUE) > 1e-7) {
    return(is.finite(n) & n == 8)
  }
  lab <- attr(grade_v, "labels", exact = FALSE)
  if (is.null(lab) || !length(lab) || !length(names(lab))) {
    return(rep(FALSE, length(grade_v)))
  }
  hit <- grepl(
    "8\\s*th|grade[^0-9a-zA-Z]*8|8[^0-9a-zA-Z]*grade|year[^0-9a-zA-Z]*8",
    names(lab),
    ignore.case = TRUE
  )
  if (!any(hit)) {
    return(rep(FALSE, length(grade_v)))
  }
  g8v <- as.numeric(lab[hit])
  g8v <- g8v[is.finite(g8v)]
  if (!length(g8v)) {
    return(rep(FALSE, length(grade_v)))
  }
  is.finite(n) & n %in% g8v
}

# --- WHO/Europe Data Warehouse (HBSC measures) --------------------------------

dw_fetch_measure_data <- function(base_url, measure_code, year, sleep_sec) {
  filter_str <- paste0("YEAR:", year)
  q <- list(lang = "EN", output = "data", filter = filter_str)
  url <- paste0(
    sub("/$", "", base_url),
    "/api/v5/measures/",
    utils::URLencode(measure_code, reserved = TRUE),
    "?",
    paste(
      names(q),
      vapply(q, utils::URLencode, character(1), reserved = TRUE),
      sep = "=",
      collapse = "&"
    )
  )

  last_msg <- NULL
  for (attempt in seq_len(5)) {
    Sys.sleep(sleep_sec)
    out <- tryCatch(
      jsonlite::fromJSON(url, simplifyVector = TRUE),
      error = function(e) e
    )
    if (!inherits(out, "error") &&
          is.list(out) &&
          is.data.frame(out$data) &&
          nrow(out$data) > 0) {
      return(out$data)
    }
    if (inherits(out, "error")) {
      last_msg <- conditionMessage(out)
    } else if (is.list(out) && !is.null(out$message)) {
      last_msg <- as.character(out$message)
    } else {
      last_msg <- "empty or invalid `data` in API response"
    }
    if (attempt < 5) {
      message("Retrying WHO DW request (attempt ", attempt + 1, "): ", last_msg)
      Sys.sleep(sleep_sec * attempt * 2)
    }
  }
  stop(
    "Failed to fetch measure ", measure_code, " from WHO Data Warehouse.\n",
    "Last message: ", last_msg
  )
}

# WHO DW uses some codes that differ from PISA CNT (ISO3).
who_dw_to_pisa_cnt <- c(
  "BE-VLG" = "BEL",
  "BE-WAL" = "BEL",
  "GB-ENG" = "GBR",
  "GB-SCT" = "GBR",
  "GB-WLS" = "GBR"
)

#' Country-level value: mean of FEMALE and MALE rows (15YO), matching PISA age group.
dw_country_values_from_facts <- function(facts_tbl, year_chr, age_grp, pisa_country_codes) {
  if (!nrow(facts_tbl)) {
    return(data.frame(cnt = character(), val = numeric(), stringsAsFactors = FALSE))
  }

  if (!all(c("dimensions", "value") %in% names(facts_tbl))) {
    stop("Unexpected WHO DW JSON: facts table needs dimensions and value columns")
  }

  d <- facts_tbl$dimensions
  vnum <- facts_tbl$value$numeric
  if (is.null(vnum)) {
    vnum <- suppressWarnings(as.numeric(facts_tbl$value$display))
  }

  df <- data.frame(
    cnt = as.character(d$COUNTRY),
    year = as.character(d$YEAR),
    age = as.character(d$AGE_GRP_2),
    sex = as.character(d$SEX),
    val = as.numeric(vnum),
    stringsAsFactors = FALSE
  )

  allow_cnt <- union(pisa_country_codes, names(who_dw_to_pisa_cnt))

  df <- df |>
    dplyr::filter(
      .data$year == year_chr,
      .data$age == age_grp,
      .data$sex %in% c("FEMALE", "MALE"),
      nzchar(.data$cnt),
      .data$cnt %in% allow_cnt,
      is.finite(.data$val)
    )

  if (!nrow(df)) {
    return(data.frame(cnt = character(), val = numeric(), stringsAsFactors = FALSE))
  }

  cv <- df |>
    dplyr::group_by(.data$cnt) |>
    dplyr::summarise(val = mean(.data$val, na.rm = TRUE), .groups = "drop")

  hit <- cv$cnt %in% names(who_dw_to_pisa_cnt)
  cv$cnt[hit] <- unname(who_dw_to_pisa_cnt[cv$cnt[hit]])

  cv |>
    dplyr::group_by(.data$cnt) |>
    dplyr::summarise(val = mean(.data$val, na.rm = TRUE), .groups = "drop") |>
    dplyr::filter(.data$cnt %in% pisa_country_codes)
}

fetch_hbsc_who_dw <- function(
    base_url,
    measure_codes,
    signs,
    year_chr,
    age_grp,
    europe_codes,
    sleep_sec
) {
  if (length(measure_codes) != length(signs)) {
    stop("HBSC_DW_MEASURES and HBSC_DW_SIGN must have the same length.")
  }

  zscore <- function(x) as.numeric(scale(x))

  country_mats <- list()
  for (i in seq_along(measure_codes)) {
    mc <- measure_codes[[i]]
    message("WHO DW: fetching ", mc, " ...")
    facts <- dw_fetch_measure_data(base_url, mc, year_chr, sleep_sec = sleep_sec)
    cv <- dw_country_values_from_facts(facts, year_chr, age_grp, europe_codes)
    if (!nrow(cv)) {
      warning("No country rows for measure ", mc, "; check YEAR / AGE filters.")
    }
    names(cv)[names(cv) == "val"] <- paste0("m", i)
    country_mats[[i]] <- cv
  }

  merged <- Reduce(
    function(a, b) dplyr::full_join(a, b, by = "cnt"),
    country_mats
  )

  mcols <- paste0("m", seq_along(measure_codes))
  mat <- as.matrix(merged[, mcols, drop = FALSE])
  ok_row <- rowSums(is.finite(mat)) == ncol(mat)
  merged <- merged[ok_row, , drop = FALSE]
  mat <- as.matrix(merged[, mcols, drop = FALSE])

  zmat <- apply(mat, 2, zscore)
  if (!is.matrix(zmat)) zmat <- matrix(zmat, ncol = length(measure_codes))
  scored <- sweep(zmat, 2, signs, `*`)
  merged$hbsc_composite <- rowMeans(scored, na.rm = TRUE)

  merged |>
    dplyr::transmute(
      cnt = .data$cnt,
      hbsc_composite = .data$hbsc_composite
    ) |>
    dplyr::filter(is.finite(.data$hbsc_composite))
}

# --- HBSC data-browser CSV (data.csv + metadata.csv) --------------------------

hbsc_browser_row_value <- function(girl, boy, sort_gender, age_group_total) {
  ag <- suppressWarnings(as.numeric(age_group_total))
  sg <- suppressWarnings(as.numeric(sort_gender))
  g <- suppressWarnings(as.numeric(girl))
  b <- suppressWarnings(as.numeric(boy))
  if (is.finite(ag)) {
    return(ag)
  }
  if (is.finite(sg)) {
    return(sg)
  }
  if (is.finite(g) && is.finite(b)) {
    return((g + b) / 2)
  }
  NA_real_
}

hbsc_browser_name_to_cnt <- c(
  "Albania" = "ALB",
  "Armenia" = "ARM",
  "Austria" = "AUT",
  "Belgium (Flanders)" = "BEL",
  "Belgium (Flemish)" = "BEL",
  "Belgium (French)" = "BEL",
  "Belgium (Wallonia)" = "BEL",
  "Bulgaria" = "BGR",
  "Canada" = "CAN",
  "Croatia" = "HRV",
  "Cyprus" = "CYP",
  "Czechia" = "CZE",
  "Denmark" = "DNK",
  "England" = "ENG",
  "Estonia" = "EST",
  "Finland" = "FIN",
  "France" = "FRA",
  "Germany" = "DEU",
  "Greece" = "GRC",
  "Greenland" = "GRL",
  "Hungary" = "HUN",
  "Iceland" = "ISL",
  "Ireland" = "IRL",
  "Italy" = "ITA",
  "Kazakhstan" = "KAZ",
  "Kyrgyzstan" = "KGZ",
  "Kyrgyztan" = "KGZ",
  "Latvia" = "LVA",
  "Lithuania" = "LTU",
  "Luxembourg" = "LUX",
  "Malta" = "MLT",
  "Netherlands" = "NLD",
  "North Macedonia" = "MKD",
  "Norway" = "NOR",
  "Poland" = "POL",
  "Portugal" = "PRT",
  "Republic of Moldova" = "MDA",
  "Romania" = "ROU",
  "Scotland" = "SCT",
  "Serbia" = "SRB",
  "Slovakia" = "SVK",
  "Slovenia" = "SVN",
  "Spain" = "ESP",
  "Sweden" = "SWE",
  "Switzerland" = "CHE",
  "Tajikistan" = "TJK",
  "Wales" = "WLS"
)

fetch_hbsc_browser_csv <- function(
    data_path,
    meta_path,
    data_url,
    meta_url,
    survey_year,
    age_label,
    measure_ids
) {
  dir.create(dirname(data_path), recursive = TRUE, showWarnings = FALSE)
  if (Sys.getenv("HBSC_BROWSER_SKIP_DOWNLOAD", "") != "1") {
    if (!file.exists(data_path) || file.size(data_path) < 1000) {
      message("Downloading HBSC data.csv ...")
      download.file(data_url, data_path, mode = "wb")
    }
    if (!file.exists(meta_path) || file.size(meta_path) < 100) {
      message("Downloading HBSC metadata.csv ...")
      download.file(meta_url, meta_path, mode = "wb")
    }
  } else if (!file.exists(data_path)) {
    stop("HBSC data file missing: ", data_path)
  }

  raw <- utils::read.csv(data_path, stringsAsFactors = FALSE, check.names = TRUE)
  nms <- names(raw)
  if (!all(c("HBSC_id", "Country", "Survey_year", "Age_group") %in% nms)) {
    stop("HBSC data.csv: expected columns HBSC_id, Country, Survey_year, Age_group")
  }
  girl_c <- if ("Girl" %in% nms) "Girl" else stop("HBSC data.csv: column Girl not found")
  boy_c <- if ("Boy" %in% nms) "Boy" else stop("HBSC data.csv: column Boy not found")
  sg_c <- if ("sort_gender" %in% nms) "sort_gender" else stop("HBSC data.csv: column sort_gender not found")
  ag_c <- if ("Age_group_total" %in% nms) "Age_group_total" else stop("HBSC data.csv: column Age_group_total not found")

  d <- raw |>
    dplyr::filter(
      .data[["HBSC_id"]] %in% measure_ids,
      nzchar(as.character(.data[["Survey_year"]])),
      suppressWarnings(as.integer(.data[["Survey_year"]])) == as.integer(survey_year),
      .data[["Age_group"]] == age_label,
      !grepl("^HBSC AVERAGE", .data[["Country"]], ignore.case = TRUE)
    )
  d$cnt <- unname(hbsc_browser_name_to_cnt[as.character(d$Country)])
  d <- d[!is.na(d$cnt), , drop = FALSE]
  d$val <- mapply(
    hbsc_browser_row_value,
    d[[girl_c]],
    d[[boy_c]],
    d[[sg_c]],
    d[[ag_c]]
  )
  d <- d[is.finite(d$val), , drop = FALSE]
  d <- d |>
    dplyr::group_by(.data$cnt, .data[["HBSC_id"]]) |>
    dplyr::summarise(val = mean(.data$val, na.rm = TRUE), .groups = "drop")

  wide <- d |>
    tidyr::pivot_wider(names_from = "HBSC_id", values_from = "val")

  miss <- setdiff(measure_ids, names(wide))
  if (length(miss)) {
    stop("Missing HBSC measures after pivot: ", paste(miss, collapse = ", "))
  }

  zscore <- function(x) as.numeric(scale(x))
  mat <- as.matrix(wide[, measure_ids, drop = FALSE])
  ok_row <- rowSums(is.finite(mat)) == length(measure_ids)
  wide <- wide[ok_row, , drop = FALSE]
  mat <- as.matrix(wide[, measure_ids, drop = FALSE])
  zmat <- apply(mat, 2, zscore)
  if (!is.matrix(zmat)) {
    zmat <- matrix(zmat, ncol = length(measure_ids))
  }
  wide$hbsc_composite <- rowMeans(zmat, na.rm = TRUE)

  wide |>
    dplyr::transmute(
      cnt = .data$cnt,
      hbsc_composite = .data$hbsc_composite
    ) |>
    dplyr::filter(.data$cnt %in% europe_iso3, is.finite(.data$hbsc_composite))
}

# --- HBSC source selection ----------------------------------------------------

hbsc_source <- tolower(Sys.getenv("HBSC_SOURCE", unset = "browser_csv"))
who_base <- Sys.getenv("WHO_DW_BASE", unset = "https://dw.euro.who.int")
hbsc_csv <- Sys.getenv("HBSC_COMPOSITE_CSV", unset = "")
hbsc_sav <- Sys.getenv("HBSC_INTERNATIONAL_SAV", unset = file.path("data", "HBSC_2018_int.sav"))

hbsc_browser_data_url <- Sys.getenv(
  "HBSC_BROWSER_DATA_URL",
  unset = "https://data-browser.hbsc.org/wp-content/uploads/csvs/data.csv"
)
hbsc_browser_meta_url <- Sys.getenv(
  "HBSC_BROWSER_META_URL",
  unset = "https://data-browser.hbsc.org/wp-content/uploads/csvs/metadata.csv"
)
hbsc_browser_data_path <- Sys.getenv(
  "HBSC_BROWSER_DATA_PATH",
  unset = file.path("data", "hbsc_data.csv")
)
hbsc_browser_meta_path <- Sys.getenv(
  "HBSC_BROWSER_META_PATH",
  unset = file.path("data", "hbsc_metadata.csv")
)

if (hbsc_source %in% c("browser_csv", "browser", "csv_browser", "data_browser")) {
  y_br <- as.integer(Sys.getenv("HBSC_BROWSER_YEAR", unset = "2022"))
  if (is.na(y_br)) {
    y_br <- 2022L
  }
  age_br <- Sys.getenv("HBSC_BROWSER_AGE", unset = "15-year-olds")
  meas_br <- trimws(
    strsplit(
      Sys.getenv(
        "HBSC_BROWSER_MEASURES",
        unset = "who5_high,lifesat_mean,d_selfeff_sol,d_selfeff_do"
      ),
      ",",
      fixed = TRUE
    )[[1]]
  )
  message(
    "HBSC via data-browser CSV (",
    hbsc_browser_data_path,
    "): measures ",
    paste(meas_br, collapse = ", "),
    ", year ",
    y_br,
    ", age ",
    age_br
  )
  hbsc_country <- fetch_hbsc_browser_csv(
    hbsc_browser_data_path,
    hbsc_browser_meta_path,
    hbsc_browser_data_url,
    hbsc_browser_meta_url,
    survey_year = y_br,
    age_label = age_br,
    measure_ids = meas_br
  )
  hbsc_x_label <- paste0(
    "HBSC composite (data-browser: ",
    paste(meas_br, collapse = ", "),
    "; z-mean across countries)"
  )
} else if (hbsc_source %in% c("who_dw", "who", "gateway", "dw")) {
  meas_str <- Sys.getenv(
    "HBSC_DW_MEASURES",
    unset = "HBSC_15,HBSC_16,HBSC_42"
  )
  sign_str <- Sys.getenv("HBSC_DW_SIGN", unset = "1,-1,1")
  year_dw <- Sys.getenv("HBSC_DW_YEAR", unset = "2018")
  age_dw <- Sys.getenv("HBSC_DW_AGE", unset = "15YO")
  sleep_dw <- as.numeric(Sys.getenv("HBSC_DW_SLEEP_SEC", unset = "2"))
  if (is.na(sleep_dw)) sleep_dw <- 2

  measure_codes <- trimws(strsplit(meas_str, ",", fixed = TRUE)[[1]])
  signs <- as.numeric(trimws(strsplit(sign_str, ",", fixed = TRUE)[[1]]))
  if (any(is.na(signs)) || !all(signs %in% c(-1, 1))) {
    stop("HBSC_DW_SIGN must be comma-separated 1 or -1 values.")
  }

  message(
    "HBSC via WHO Data Warehouse (",
    who_base,
    "): measures ",
    paste(measure_codes, collapse = ", "),
    ", year ",
    year_dw,
    ", age ",
    age_dw
  )

  hbsc_country <- fetch_hbsc_who_dw(
    who_base,
    measure_codes,
    signs,
    year_chr = year_dw,
    age_grp = age_dw,
    europe_codes = europe_iso3,
    sleep_sec = sleep_dw
  )

  hbsc_x_label <- paste0(
    "HBSC composite (WHO DW: ",
    paste(measure_codes, collapse = ", "),
    "; z-scored, signs ",
    paste(as.character(signs), collapse = ","),
    ")"
  )
} else if (hbsc_source == "csv" && nzchar(hbsc_csv) && file.exists(hbsc_csv)) {
  message("Reading HBSC country composites from CSV: ", hbsc_csv)
  hbsc_country <- utils::read.csv(hbsc_csv, stringsAsFactors = FALSE)
  if (!all(c("cnt", "hbsc_composite") %in% names(hbsc_country))) {
    stop("HBSC_COMPOSITE_CSV must have columns: cnt, hbsc_composite")
  }
  hbsc_country <- hbsc_country |>
    dplyr::transmute(
      cnt = toupper(as.character(.data$cnt)),
      hbsc_composite = as.numeric(.data$hbsc_composite)
    ) |>
    dplyr::filter(.data$cnt %in% europe_iso3, is.finite(.data$hbsc_composite))
  hbsc_x_label <- "HBSC composite (user CSV)"
} else if (hbsc_source == "sav" && file.exists(hbsc_sav)) {
  message("Reading HBSC international file: ", hbsc_sav)
  hbsc <- haven::read_sav(hbsc_sav)
  nms <- names(hbsc)

  cnt_h <- first_present(nms, c("cnt", "CNT", "cnty", "CNTY", "country", "COUNTRY", "region", "REGION"))
  if (is.na(cnt_h)) stop("Could not find HBSC country column (tried cnt, cnty, country, region).")

  life <- first_present(
    nms,
    c("lifesat", "LIFESAT", "ls", "LS", "lifesat0", "cantril", "CANTRIL")
  )
  who <- first_present(nms, c("who5", "WHO5", "who5tot", "WHO5TOT", "wh5sc", "WH5SC"))
  seff1 <- first_present(nms, c("seffgoals", "SEFFGOALS", "seff_g", "effgoals"))
  seff2 <- first_present(nms, c("seffprob", "SEFFPROB", "seff_p", "effprob"))

  if (is.na(life)) {
    stop("Could not find life satisfaction column in HBSC file (tried lifesat, ls, cantril, ...).")
  }

  who5_items <- grep("^who5b?[0-5]$|^WHO5B?[0-5]$", nms, value = TRUE)
  if (is.na(who) && length(who5_items) >= 5) {
    hbsc <- hbsc |>
      dplyr::mutate(
        `_who5_sum` = rowSums(
          dplyr::across(dplyr::all_of(who5_items), \(x) as.numeric(x)),
          na.rm = FALSE
        )
      )
    who <- "_who5_sum"
  }
  if (is.na(who)) {
    stop("Could not find WHO-5 total or WHO-5 items (who5b1–who5b5) in HBSC file.")
  }

  if (!is.na(seff1) && !is.na(seff2)) {
    hbsc <- hbsc |>
      dplyr::mutate(
        `_seff` = (as.numeric(.data[[seff1]]) + as.numeric(.data[[seff2]])) / 2
      )
    seff_col <- "_seff"
  } else if (!is.na(seff1)) {
    hbsc <- hbsc |>
      dplyr::mutate(`_seff` = as.numeric(.data[[seff1]]))
    seff_col <- "_seff"
  } else {
    stop("Could not find self-efficacy items (seffgoals / seffprob).")
  }

  cnt_raw <- hbsc[[cnt_h]]
  cnt_chr <- if (inherits(cnt_raw, "labelled")) {
    as.character(haven::as_factor(cnt_raw))
  } else {
    as.character(cnt_raw)
  }

  hbsc_df <- hbsc |>
    dplyr::mutate(
      .cnt = cnt_chr,
      .life = as.numeric(.data[[life]]),
      .who = as.numeric(.data[[who]]),
      .seff = as.numeric(.data[[seff_col]])
    ) |>
    dplyr::filter(is.finite(.data$.life), is.finite(.data$.who), is.finite(.data$.seff))

  region_fix <- c(
    "Czechia" = "CZE",
    "Czech Republic" = "CZE",
    "United Kingdom" = "GBR",
    "England" = "GBR",
    "Scotland" = "GBR",
    "Wales" = "GBR",
    "North Macedonia" = "MKD",
    "Moldova" = "MDA",
    "Republic of Moldova" = "MDA",
    "Türkiye" = "TUR",
    "Turkey" = "TUR",
    "Russian Federation" = "RUS",
    "Kyrgyzstan" = "KGZ",
    "Kyrgyztan" = "KGZ"
  )

  map_region_label <- function(ch) {
    hit <- region_fix[ch]
    if (!is.na(hit)) as.character(hit) else ch
  }

  hbsc_df <- hbsc_df |>
    dplyr::mutate(cnt = vapply(.data$.cnt, map_region_label, character(1)))

  hbsc_df <- hbsc_df |>
    dplyr::mutate(
      cnt = dplyr::if_else(
        grepl("^[A-Z]{3}$", .data$cnt),
        .data$cnt,
        NA_character_
      )
    ) |>
    tidyr::drop_na(.data$cnt)

  zscore <- function(x) as.numeric(scale(x))

  hbsc_country <- hbsc_df |>
    dplyr::mutate(
      hbsc_composite = (
        zscore(.data$.life) + zscore(.data$.who) + zscore(.data$.seff)
      ) / 3
    ) |>
    dplyr::group_by(.data$cnt) |>
    dplyr::summarise(hbsc_composite = mean(.data$hbsc_composite, na.rm = TRUE), .groups = "drop") |>
    dplyr::filter(.data$cnt %in% europe_iso3)
  hbsc_x_label <- "HBSC composite (z-mean of life satisfaction, WHO-5, self-efficacy; microdata)"
} else {
  stop(
    "No HBSC input configured.\n",
    "Default is HBSC data-browser CSV: HBSC_SOURCE=browser_csv (or unset).\n",
    "Alternatively: HBSC_SOURCE=who_dw (WHO API), HBSC_SOURCE=csv with HBSC_COMPOSITE_CSV,\n",
    "or HBSC_SOURCE=sav with HBSC_INTERNATIONAL_SAV.\n",
    "WHO API: https://gateway.euro.who.int/en/api/specification/\n",
    "HBSC microdata (UiB): https://www.uib.no/en/hbscdata/113290/open-access"
  )
}

# --- PISA 2022 (Zenodo record 13382904, CY08MSP_STU_QQQ.sav) -----------------

pisa_path <- file.path(cache_dir, pisa_filename)
# Zenodo CY08MSP_STU_QQQ.sav is ~1.97 GB; drop truncated caches from failed downloads.
pisa_min_bytes <- as.numeric(Sys.getenv("PISA_MIN_BYTES", unset = "1900000000"))
if (is.na(pisa_min_bytes)) pisa_min_bytes <- 1900000000
if (file.exists(pisa_path) && file.size(pisa_path) < pisa_min_bytes) {
  message(
    "Removing incomplete PISA cache (",
    file.size(pisa_path),
    " bytes; expected at least ",
    pisa_min_bytes,
    ")."
  )
  unlink(pisa_path)
}

if (!file.exists(pisa_path) && Sys.getenv("PISA_SKIP_DOWNLOAD", "") != "1") {
  message("Downloading PISA 2022 student file from Zenodo (~2 GB). This can take a while.")
  to <- as.integer(Sys.getenv("PISA_DOWNLOAD_TIMEOUT_SEC", unset = "7200"))
  if (is.na(to) || to < 60) to <- 7200
  options(timeout = max(to, getOption("timeout")))
  download.file(zenodo_stu_url, pisa_path, mode = "wb")
} else if (!file.exists(pisa_path)) {
  stop("PISA file missing: ", pisa_path)
}

max_rows <- Sys.getenv("PISA_MAX_ROWS", unset = "")
n_max <- if (nzchar(max_rows)) as.integer(max_rows) else Inf
if (is.na(n_max)) n_max <- Inf

message("Reading PISA student file...")
if (is.finite(n_max)) {
  pisa <- haven::read_sav(pisa_path, n_max = n_max)
} else {
  pisa <- haven::read_sav(pisa_path)
}

pv_read <- if ("PV1READ" %in% names(pisa)) "PV1READ" else stop("PV1READ not found in PISA file")
pv_math <- if ("PV1MATH" %in% names(pisa)) "PV1MATH" else stop("PV1MATH not found in PISA file")
pv_scie <- if ("PV1SCIE" %in% names(pisa)) {
  "PV1SCIE"
} else if ("PV1SCI" %in% names(pisa)) {
  "PV1SCI"
} else {
  stop("Neither PV1SCIE nor PV1SCI found in PISA file")
}

cnt_col <- if ("CNT" %in% names(pisa)) "CNT" else stop("CNT not found in PISA file")
w_col <- if ("W_FSTUWT" %in% names(pisa)) "W_FSTUWT" else stop("W_FSTUWT not found in PISA file")

# PISA: Europe + optional grade 8; z-domain PV1s within this analytic sample, then mean → composite, then country WTM.
pisa_use_g8 <- Sys.getenv("PISA_USE_GRADE8", unset = "0") != "0"
n_p <- nrow(pisa)
pisa_g8_ok <- if (pisa_use_g8) {
  gr_name <- first_present(
    names(pisa),
    c("ST001Q01TA", "ST001Q01T", "ST01Q01TA", "GRADE")
  )
  if (is.na(gr_name)) {
    stop(
      "PISA: no grade column (tried ST001Q01TA, ST001Q01T, ST01Q01TA, GRADE). ",
      "Set PISA_USE_GRADE8=0 to use all 15-year-olds (default), or add the grade column to the file."
    )
  }
  message("PISA: restricting to grade 8 with column: ", gr_name, " (PISA 2022).")
  pisa_is_grade8(pisa[[gr_name]])
} else {
  rep(TRUE, n_p)
}

cnt_p <- as.character(pisa[[cnt_col]])
w_p <- as.numeric(pisa[[w_col]])
pvr_p <- as.numeric(pisa[[pv_read]])
pvm_p <- as.numeric(pisa[[pv_math]])
pvs_p <- as.numeric(pisa[[pv_scie]])
ok_p <-
  pisa_g8_ok &
  (cnt_p %in% europe_iso3) &
  (is.finite(w_p) & w_p > 0) &
  is.finite(pvr_p) &
  is.finite(pvm_p) &
  is.finite(pvs_p)
pisa_df <- data.frame(
  cnt = cnt_p[ok_p],
  w = w_p[ok_p],
  pv_read = pvr_p[ok_p],
  pv_math = pvm_p[ok_p],
  pv_scie = pvs_p[ok_p],
  stringsAsFactors = FALSE
)

if (nrow(pisa_df) < 2L) {
  stop(
    "PISA: too few students after Europe + (optional) grade-8 + valid PV1 filters. ",
    "If grade-8 codes differ in your file, set PISA_GRADE8_CODES (comma-separated integers)."
  )
}
if (pisa_use_g8 && mean(pisa_g8_ok) < 0.001) {
  warning("Very few PISA students flagged as grade 8; check PISA_GRADE8_CODES and ST001Q01TA labels.")
}
z1 <- as.numeric(scale(pisa_df$pv_read, center = TRUE, scale = TRUE))
z2 <- as.numeric(scale(pisa_df$pv_math, center = TRUE, scale = TRUE))
z3 <- as.numeric(scale(pisa_df$pv_scie, center = TRUE, scale = TRUE))
pisa_df$pisa_composite <- (z1 + z2 + z3) / 3

pisa_country <- pisa_df |>
  dplyr::group_by(.data$cnt) |>
  dplyr::summarise(
    pisa_composite = stats::weighted.mean(.data$pisa_composite, .data$w, na.rm = TRUE),
    .groups = "drop"
  )

nordic <- c("DNK", "FIN", "ISL", "NOR", "SWE")

pisa_ylabel <- if (pisa_use_g8) {
  "PISA composite (z-mean of PV1 reading, math, science; z within grade-8, Europe)"
} else {
  "PISA composite (z-mean of PV1 reading, math, science; z within 15-year-old sample, Europe)"
}

merged <- dplyr::inner_join(hbsc_country, pisa_country, by = "cnt") |>
  dplyr::mutate(
    is_nordic = .data$cnt %in% nordic,
    region_plot = dplyr::case_when(
      .data$cnt == "NOR" ~ "Norway",
      .data$is_nordic ~ "Other Nordic",
      TRUE ~ "Other Europe"
    ),
    pt_size = dplyr::case_when(
      .data$cnt == "NOR" ~ 4.5,
      .data$is_nordic ~ 3.0,
      TRUE ~ 2.0
    )
  )

if (nrow(merged) < 5) {
  warning("Very few matched countries (", nrow(merged), "). Check HBSC country coding vs PISA CNT.")
}

p <- ggplot2::ggplot(merged, ggplot2::aes(hbsc_composite, pisa_composite)) +
  ggplot2::geom_point(
    ggplot2::aes(color = region_plot, size = pt_size),
    alpha = 0.88,
    show.legend = TRUE
  ) +
  ggplot2::scale_color_manual(
    name = NULL,
    values = c(
      "Norway" = "#c0392b",
      "Other Nordic" = "#e67e22",
      "Other Europe" = "#2980b9"
    ),
    breaks = c("Norway", "Other Nordic", "Other Europe")
  ) +
  ggplot2::scale_size_identity(guide = "none") +
  ggplot2::geom_text(
    data = dplyr::filter(merged, is_nordic),
    ggplot2::aes(
      hbsc_composite,
      pisa_composite,
      label = cnt,
      fontface = ifelse(cnt == "NOR", "bold", "plain")
    ),
    vjust = -0.9,
    size = 3.2
  ) +
  ggplot2::labs(
    x = hbsc_x_label,
    y = pisa_ylabel,
    title = if (pisa_use_g8) {
      "Adolescent well-being (HBSC) and learning (PISA) by country (PISA: grade 8, Europe)"
    } else {
      "Adolescent well-being (HBSC) and learning (PISA) by country (PISA: 15-year-olds, Europe)"
    }
  ) +
  ggplot2::theme_bw() +
  ggplot2::theme(legend.position = "bottom")

ggplot2::ggsave(out_png, p, width = 8, height = 5.5, dpi = 150)
message("Wrote ", normalizePath(out_png, winslash = "/", mustWork = FALSE))
