/** A box in an element's frame, in pixels. */
export type Area = { x: number; y: number; width: number; height: number }

/** The box of `element`'s section across the whole page, in `element`'s own frame: from the
 * page's left edge to its right one, the section's top to its bottom. */
export function sectionArea(element: HTMLElement): Area {
  const here = element.getBoundingClientRect()
  const section = element.closest("section")!.getBoundingClientRect()
  const page = document.body.getBoundingClientRect()

  return {
    x: page.left - here.left,
    y: section.top - here.top,
    width: page.width,
    height: section.height,
  }
}
