import { createHmac, timingSafeEqual } from "node:crypto"

import { PREVIEW_SIGNATURE_LENGTH } from "@/constants/preview-image"

/** The signature of a link-preview picture's title and language, so /preview draws only the
 * titles prepza's own pages name. Without PREVIEW_SECRET (local and CI) it signs with an empty
 * key, which still matches itself. */
export function previewSignature(title: string, locale: string) {
  return createHmac("sha256", process.env.PREVIEW_SECRET ?? "")
    .update(`${locale}\n${title}`)
    .digest("hex")
    .slice(0, PREVIEW_SIGNATURE_LENGTH)
}

export function validPreviewSignature(
  title: string,
  locale: string,
  signature: string
) {
  const expected = Buffer.from(previewSignature(title, locale))
  const given = Buffer.from(signature)

  return given.length === expected.length && timingSafeEqual(given, expected)
}
