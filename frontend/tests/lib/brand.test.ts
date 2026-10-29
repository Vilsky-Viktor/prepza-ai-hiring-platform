import { expect, it } from "vitest"

import { brandStyle, pickTheme } from "@/lib/brand"

const COLORS = {
  background: "#101418",
  foreground: "#f4f1ea",
  card: "#1d242c",
  card_foreground: "#f4f1ea",
  primary: "#ff7a1a",
  primary_foreground: "#1a1007",
  muted: "#1d242c",
  muted_foreground: "#a9b4bf",
  border: "#2c3640",
}

it("sets every theme variable the candidate's pages use", () => {
  const style = brandStyle(COLORS)

  expect(style["--background"]).toBe("#101418")
  // Dialogs and menus take the dialogs' colors, the focus ring the primary.
  expect(style["--popover"]).toBe("#1d242c")
  expect(style["--ring"]).toBe("#ff7a1a")
  expect(style["--input"]).toBe("#2c3640")
})

it("sets the titles' font over the site's Poppins and the text's over its Geist", () => {
  const look = { radius: 14, buttonRadius: 14 }

  expect(
    brandStyle(COLORS, { ...look, headingFont: "Lora", textFont: "Inter" })
  ).toMatchObject({ "--font-poppins": "Lora", "--font-geist": "Inter" })
  // None given: the site's own stays.
  expect(brandStyle(COLORS, look)).not.toHaveProperty("--font-poppins")
  expect(brandStyle(COLORS, look)).not.toHaveProperty("--font-geist")
})

it("shows the theme the address asks for, else the invite's, else the visitor's", () => {
  expect(pickTheme("dark", "light", "light")).toBe("dark")
  expect(pickTheme("default", "dark", "light")).toBe("light")
  expect(pickTheme(null, "dark", "light")).toBe("dark")
  expect(pickTheme("sepia", null, "dark")).toBe("dark")
})
