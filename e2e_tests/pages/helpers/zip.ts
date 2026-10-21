import { inflateRawSync } from "node:zlib"

// A ZIP entry's local header: its signature, then its name and data after 30 bytes.
const LOCAL_HEADER = 0x04034b50
const STORED = 0
const DEFLATED = 8

/** Each file in a ZIP, by name: read from its local headers in order, unpacked. */
export function zipEntries(zip: Buffer): Map<string, Buffer> {
  const entries = new Map<string, Buffer>()
  let offset = 0

  while (offset + 30 <= zip.length && zip.readUInt32LE(offset) === LOCAL_HEADER) {
    const method = zip.readUInt16LE(offset + 8)
    const size = zip.readUInt32LE(offset + 18)
    const nameLength = zip.readUInt16LE(offset + 26)
    const extraLength = zip.readUInt16LE(offset + 28)
    const start = offset + 30 + nameLength + extraLength
    const name = zip.subarray(offset + 30, offset + 30 + nameLength).toString("utf8")
    const data = zip.subarray(start, start + size)

    if (method !== STORED && method !== DEFLATED) {
      throw new Error(`${name}: unsupported compression ${method}`)
    }

    entries.set(name, method === DEFLATED ? inflateRawSync(data) : data)
    offset = start + size
  }

  return entries
}
