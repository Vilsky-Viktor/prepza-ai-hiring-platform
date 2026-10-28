"use client"

import { cn } from "cn"
import { ImageUpIcon, SquarePenIcon, Trash2Icon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useRef, useState } from "react"
import { toast } from "sonner"

import { CompanyLogo } from "@/components/common/company-logo"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { apiFetch, serviceRefusal } from "@/lib/api"
import { fileBase64 } from "@/lib/files"
import { firstGrapheme } from "@/lib/graphemes"

const BOX =
  "flex size-12 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-surface"
const LARGE = "size-24 rounded-xl"
const SPOT = `${BOX} group relative cursor-pointer transition-colors hover:bg-surface disabled:cursor-default`

/** The company's logo beside its name: without one, its first letter, and a click picks an
 * image; with one, a click offers to change or remove it. Not `editable` (a viewer), it only
 * shows. */
export function LogoPicker({
  companyId,
  name,
  logoUrl,
  editable,
  large = false,
}: {
  companyId: string
  name: string
  logoUrl: string | null
  editable: boolean
  // Twice the size: the brand tab's, where it's set.
  large?: boolean
}) {
  const t = useTranslations("company")
  const router = useRouter()
  const fileInput = useRef<HTMLInputElement>(null)
  const [saving, setSaving] = useState(false)
  const path = `/companies/companies/${companyId}/logo`

  async function save(request: () => Promise<unknown>) {
    setSaving(true)

    try {
      await request()
      router.refresh()
    } catch (error) {
      // A file that isn't a PNG, JPEG or WebP up to 500 KB: the API says so.
      toast.error(
        serviceRefusal(error, [403, 404, 413, 422]) ?? t("logoFailed")
      )
    } finally {
      setSaving(false)
    }
  }

  function upload(file: File | undefined) {
    if (file) {
      save(async () =>
        apiFetch(path, {
          method: "PUT",
          body: JSON.stringify({ image: await fileBase64(file) }),
        })
      )
    }
  }

  const picker = (
    <input
      ref={fileInput}
      type="file"
      accept="image/png,image/jpeg,image/webp"
      className="hidden"
      onChange={(event) => {
        upload(event.target.files?.[0])
        event.target.value = ""
      }}
    />
  )

  const letter = (
    <span
      className={cn(
        "font-heading text-2xl font-medium text-muted-foreground uppercase",
        large && "text-4xl"
      )}
    >
      {firstGrapheme(name)}
    </span>
  )

  // An edit icon in the corner says it can be changed; on hover, a bigger one in the middle.
  const editHint = (
    <>
      <span
        aria-hidden
        className="absolute end-1 top-1 flex rounded-lg bg-background/90 p-0.5 text-muted-foreground transition-opacity group-hover:opacity-0 group-focus-visible:opacity-0"
      >
        <SquarePenIcon
          className={cn("size-3 rtl:-scale-x-100", large && "size-4")}
        />
      </span>
      <span
        aria-hidden
        className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
      >
        <SquarePenIcon
          className={cn(
            "size-5 text-white rtl:-scale-x-100",
            large && "size-7"
          )}
        />
      </span>
    </>
  )

  if (!editable) {
    return (
      <span className={cn(BOX, large && LARGE)}>
        {logoUrl ? (
          <CompanyLogo
            url={logoUrl}
            name={name}
            className="size-full object-contain"
          />
        ) : (
          letter
        )}
      </span>
    )
  }

  if (!logoUrl) {
    return (
      <>
        <Tooltip>
          <TooltipTrigger
            render={
              <button
                type="button"
                className={cn(SPOT, large && LARGE)}
                disabled={saving}
                aria-label={t("uploadLogo")}
                onClick={() => fileInput.current?.click()}
              />
            }
          >
            {letter}
            {editHint}
          </TooltipTrigger>
          <TooltipContent>{t("uploadLogo")}</TooltipContent>
        </Tooltip>
        {picker}
      </>
    )
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <button
              type="button"
              className={cn(SPOT, large && LARGE)}
              disabled={saving}
              aria-label={t("logo")}
            />
          }
        >
          <CompanyLogo
            url={logoUrl}
            name={name}
            className="size-full object-contain"
          />
          {editHint}
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-48 p-2">
          <DropdownMenuItem
            className="px-3 py-2"
            onClick={() => fileInput.current?.click()}
          >
            <ImageUpIcon />
            {t("changeLogo")}
          </DropdownMenuItem>
          <DropdownMenuItem
            className="px-3 py-2"
            onClick={() => save(() => apiFetch(path, { method: "DELETE" }))}
          >
            <Trash2Icon />
            {t("removeLogo")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      {picker}
    </>
  )
}
