import {
  LineIcon,
  TelegramIcon,
  ViberIcon,
  WhatsAppIcon,
} from "@/components/chat-icons"

// The chat apps a report's summary can be shared to, in their order on screen, each with the link
// that opens it with the text. Viber's opens only where its app is installed.
export const CHAT_APPS = [
  {
    name: "WhatsApp",
    Icon: WhatsAppIcon,
    link: (text: string) => `https://wa.me/?text=${encodeURIComponent(text)}`,
  },
  {
    name: "Telegram",
    Icon: TelegramIcon,
    link: (text: string, origin: string) =>
      `https://t.me/share/url?url=${encodeURIComponent(origin)}&text=${encodeURIComponent(text)}`,
  },
  {
    name: "Viber",
    Icon: ViberIcon,
    link: (text: string) => `viber://forward?text=${encodeURIComponent(text)}`,
  },
  {
    name: "LINE",
    Icon: LineIcon,
    link: (text: string) =>
      `https://line.me/R/share?text=${encodeURIComponent(text)}`,
  },
]
