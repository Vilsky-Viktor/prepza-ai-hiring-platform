"use client"

import { MonitorIcon, MoonIcon, SunIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useTheme } from "next-themes"

import { Button } from "@/components/ui/button"

const modes = [
  { value: "system", icon: MonitorIcon },
  { value: "light", icon: SunIcon },
  { value: "dark", icon: MoonIcon },
] as const

export function ThemeModes() {
  const t = useTranslations("userMenu")
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex w-full gap-1" role="group" aria-label={t("theme")}>
      {modes.map(({ value, icon: Icon }) => (
        <Button
          key={value}
          type="button"
          variant={theme === value ? "secondary" : "ghost"}
          className="h-8 flex-1 shrink"
          aria-label={t(value)}
          tooltip={t(value)}
          aria-pressed={theme === value}
          onClick={() => setTheme(value)}
        >
          <Icon />
        </Button>
      ))}
    </div>
  )
}
