import type en from "../messages/en.json"
import type { Locale } from "./config/i18n"

// Messages typed from the English ones: an unknown key or a missing argument fails the build.
declare module "next-intl" {
  interface AppConfig {
    Locale: Locale
    Messages: typeof en
  }
}
