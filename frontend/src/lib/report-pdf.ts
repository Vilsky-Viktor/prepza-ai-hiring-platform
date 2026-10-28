// A4 in PDF points; the report is laid out 794px wide, A4's width at 96 dpi.
const PAGE_WIDTH = 595.28
const PAGE_HEIGHT = 841.89
// The report's own padding, in px, kept as the top and bottom margin of every page.
const MARGIN = 53

/** Where each page starts and how tall it is, in the report's px: a page ends before the first
block or row that wouldn't fit, so none is cut in two. */
export function pageSlices(node: HTMLElement, pageHeight: number) {
  const top = node.getBoundingClientRect().top
  const slices = [{ start: 0, height: 0 }]

  // The report's blocks and its list's rows, in order.
  for (const row of node.querySelectorAll<HTMLElement>(
    ":scope > :not(ul), li"
  )) {
    const box = row.getBoundingClientRect()
    const slice = slices[slices.length - 1]
    const limit = pageHeight - MARGIN * (slices.length > 1 ? 2 : 1)

    if (box.bottom - top - slice.start > limit) {
      slice.height = box.top - top - slice.start
      slices.push({ start: box.top - top, height: 0 })
    }
  }

  const last = slices[slices.length - 1]
  last.height = node.offsetHeight - last.start

  return slices
}

/** The report element as an A4 PDF: a sharp picture of it. On one page, scaled down when it's
 * taller (a candidate's report); or, with `pages`, at full width over as many pages as it takes
 * (every candidate of a test), each page its own picture, so a long report never makes one
 * picture larger than the browser can draw. The libraries load only when a report is made. */
export async function reportPdf(
  node: HTMLElement,
  name: string,
  pages = false
): Promise<File> {
  const [{ toJpeg, getFontEmbedCSS }, { jsPDF }] = await Promise.all([
    import("html-to-image"),
    import("jspdf"),
  ])
  const fontEmbedCSS = await getFontEmbedCSS(node)

  // The copy is drawn in place, not off screen where the page keeps the report, shifted up to
  // the slice it shows. JPEG keeps the file small enough to send in a chat or an email.
  function picture(start: number, height: number) {
    return toJpeg(node, {
      pixelRatio: 2,
      quality: 0.9,
      backgroundColor: "#ffffff",
      fontEmbedCSS,
      height,
      style: {
        position: "static",
        left: "auto",
        transform: `translateY(-${start}px)`,
      },
    })
  }

  const pdf = new jsPDF({ unit: "pt", format: "a4" })

  if (!pages) {
    const scale = Math.min(
      PAGE_WIDTH / node.offsetWidth,
      PAGE_HEIGHT / node.offsetHeight
    )
    const width = node.offsetWidth * scale
    pdf.addImage(
      await picture(0, node.offsetHeight),
      "JPEG",
      (PAGE_WIDTH - width) / 2,
      0,
      width,
      node.offsetHeight * scale
    )

    return new File([pdf.output("blob")], name, { type: "application/pdf" })
  }

  const scale = PAGE_WIDTH / node.offsetWidth
  const slices = pageSlices(node, PAGE_HEIGHT / scale)

  for (const [page, slice] of slices.entries()) {
    if (page > 0) {
      pdf.addPage()
    }

    // The first page starts with the report's own padding; the others get the same margin.
    pdf.addImage(
      await picture(slice.start, slice.height),
      "JPEG",
      0,
      page > 0 ? MARGIN * scale : 0,
      PAGE_WIDTH,
      slice.height * scale
    )
  }

  return new File([pdf.output("blob")], name, { type: "application/pdf" })
}
