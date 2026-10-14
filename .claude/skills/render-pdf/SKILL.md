---
name: render-pdf
description: Render a styled HTML file to PDF with headless Chrome, since pandoc is not installed. Use when a report, proposal or progress document needs a PDF.
---

# HTML to PDF

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-pdf-header-footer --user-data-dir="<scratchpad>/chrome-prof" \
  --print-to-pdf="OUT.pdf" "file:///ABS/PATH/IN.html"
```

- Chrome writes the PDF and then hangs on exit. Run it in the background or with a short timeout, and
  `pkill -9 -f "Google Chrome.*headless"` once the file exists.
- Page count: `mdls -name kMDItemNumberOfPages OUT.pdf`. Preview: `qlmanage -t -s 1400 -o DIR OUT.pdf`.
- Times New Roman renders Vietnamese diacritics.
