# Generate PNG QR codes for the AI4Research blog pages (layout via magick / ImageMagick).
# Run from this folder: Rscript generate_blog_qr.R

for (p in c("qrcode", "magick")) {
  if (!requireNamespace(p, quietly = TRUE)) {
    install.packages(p, repos = "https://cloud.r-project.org")
  }
}
library(qrcode)
library(magick)

out_dir <- "."
urls <- c(
  no = "https://gbiele.github.io/AI4Research/AI4Research_blog_no.html",
  en = "https://gbiele.github.io/AI4Research/AI4Research_blog_en.html"
)
header_texts <- c(
  no = "Lenke til blogginnlegg",
  en = "Link to blog post"
)
labels <- c(no = "NO", en = "EN")

# QR square (px) + top/bottom strips; weight 700 = bold in image_annotate
px <- 400L
header_h <- 60L
header_size <- 32L
label_h <- 56L
label_size <- 36L

# White strip, centered text (bold sans)
an_strip <- function(w, h, text, size) {
  image_annotate(
    image_blank(w, h, "white"),
    text,
    size = size,
    color = "black",
    weight = 700L,
    gravity = "center",
    font = "sans"
  )
}

for (name in names(urls)) {
  tmp <- tempfile(fileext = ".png")
  grDevices::png(tmp, width = px, height = px, bg = "white")
  graphics::par(mar = rep(0L, 4L), oma = rep(0L, 4L))
  plot(qr_code(urls[[name]], ecl = "M"), asp = 1, axes = FALSE, xlab = "", ylab = "")
  grDevices::dev.off()

  img <- image_read(tmp)
  w <- image_info(img)$width
  combined <- image_append(
    c(
      an_strip(w, header_h, header_texts[[name]], header_size),
      img,
      an_strip(w, label_h, labels[[name]], label_size)
    ),
    stack = TRUE
  )
  out <- file.path(out_dir, sprintf("AI4Research_blog_%s_qr.png", name))
  image_write(combined, path = out)
  unlink(tmp)
  message("Wrote: ", normalizePath(out, winslash = "/"))
}
