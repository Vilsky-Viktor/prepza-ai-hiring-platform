"use client"

import {
  DollarSignIcon,
  ShieldCogCornerIcon,
  LogInIcon,
  LogOutIcon,
  SettingsIcon,
} from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { useSignIn } from "@/components/sign-in-dialog"
import { useAuth } from "@/components/auth-provider"
import { ThemeModes } from "@/components/theme-toggle"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { CopyIdItem } from "@/components/copy-id-item"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { apiFetch } from "@/lib/api"
import { signOut } from "@/lib/auth"
import { firstGrapheme } from "@/lib/graphemes"

export function UserMenu() {
  const t = useTranslations("userMenu")
  const signIn = useSignIn()
  const { user, loading } = useAuth()
  // The backend says whether this account may open the superadmin pages; kept by account, so a
  // different sign-in never inherits it.
  const [superadminUid, setSuperadminUid] = useState<string | null>(null)
  const superadmin = user !== null && superadminUid === user.uid

  useEffect(() => {
    if (!user) {
      return
    }

    apiFetch<{ is_superadmin: boolean }>("/library/me")
      .then((me) => setSuperadminUid(me.is_superadmin ? user.uid : null))
      .catch(() => setSuperadminUid(null))
  }, [user])

  if (loading) {
    return <div className="size-10" />
  }

  if (!user) {
    return (
      // Under 400px, where the header can't fit the label in every language, the icon alone.
      <Button
        variant="outline"
        className="px-4 max-[399px]:w-8 max-[399px]:px-0"
        aria-label={t("signIn")}
        data-testid="header-sign-in"
        onClick={() => signIn()}
      >
        <LogInIcon aria-hidden className="hidden max-[399px]:block" />
        <span aria-hidden className="max-[399px]:hidden">
          {t("signIn")}
        </span>
      </Button>
    )
  }

  const initial = firstGrapheme(
    user.displayName ?? user.email ?? "?"
  ).toUpperCase()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        data-testid="account-menu"
        render={
          <Button
            variant="ghost"
            size="icon"
            className="size-10 rounded-full"
            aria-label={t("account")}
          />
        }
      >
        <Avatar size="lg">
          <AvatarImage src={user.photoURL ?? undefined} alt="" />
          <AvatarFallback>{initial}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 p-2">
        <DropdownMenuGroup>
          <div className="flex items-start gap-1">
            <DropdownMenuLabel className="min-w-0 flex-1 px-3 py-2">
              <p className="truncate text-sm text-foreground">
                {user.displayName}
              </p>
              <p className="truncate font-normal">{user.email}</p>
            </DropdownMenuLabel>
            {/* The account's id, to quote when writing to prepza: an icon at the name's right, a
                menu item reached with the arrow keys too, that stays open to show it copied. */}
            <CopyIdItem id={user.uid} />
          </div>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="px-3 py-2"
          render={<Link href="/top-up" />}
        >
          <DollarSignIcon />
          {t("topUp")}
        </DropdownMenuItem>
        {superadmin && (
          <DropdownMenuItem
            className="px-3 py-2"
            render={<Link href="/superadmin/templates" />}
          >
            <ShieldCogCornerIcon />
            {t("adminZone")}
          </DropdownMenuItem>
        )}
        <DropdownMenuItem
          className="px-3 py-2"
          render={<Link href="/settings" />}
        >
          <SettingsIcon />
          {t("settings")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="px-3 py-2"
          variant="destructive"
          onClick={() => signOut()}
        >
          <LogOutIcon className="rtl:-scale-x-100" />
          {t("signOut")}
        </DropdownMenuItem>
        <DropdownMenuSeparator className="mb-3" />
        <ThemeModes />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
