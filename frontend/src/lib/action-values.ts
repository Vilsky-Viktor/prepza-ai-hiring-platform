import { LANGUAGE_NAMES, type Locale } from "@/constants/i18n"

// The preview fields that hold a language code, shown by the language's name.
const LANGUAGE_FIELDS = ["generate_in", "language"]

/** A card's value as text: a language by its name, a list joined, a map as "key: on" lines
 * (`yes` and `no` name true and false); anything else as it is. */
export function previewValue(
  key: string,
  value: unknown,
  yes: string,
  no: string
): string {
  if (typeof value === "boolean") {
    return value ? yes : no
  }

  if (LANGUAGE_FIELDS.includes(key) && typeof value === "string") {
    return LANGUAGE_NAMES[value as Locale] ?? value
  }

  if (Array.isArray(value)) {
    return value.map(String).join(", ")
  }

  if (value && typeof value === "object") {
    return Object.entries(value)
      .map(
        ([name, on]) =>
          `${name}: ${on === true ? yes : on === false ? no : String(on)}`
      )
      .join("\n")
  }

  return String(value)
}
