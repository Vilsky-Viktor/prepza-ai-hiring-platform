"use client"

import { ListChecksIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { Fragment, useState } from "react"
import { toast } from "sonner"

import { IconButton } from "@/components/icon-button"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { lockedReads, permissionsByGroup, tick } from "@/lib/api-permissions"
import { bdi } from "@/lib/bidi"
import { hasMessage } from "@/lib/messages"
import type { ApiKey, PermissionOptions } from "@/types/api-access"

// The sizes of the email preferences' checkboxes: "Select all" like the digest, the rest like
// its kinds. A checkbox that can't change fades with its text, as a disabled switch does.
const LABEL =
  "flex cursor-pointer items-center has-data-disabled:cursor-not-allowed has-data-disabled:opacity-50"
const BIG = "size-7 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-5"
const SMALL = "size-6 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-4"

// A group or a permission from the API by its name in `group`, or as it is when there's none.
function named(
  t: ReturnType<typeof useTranslations<"api">>,
  group: "permissionGroups" | "permissions" | "permissionLine",
  value: string
) {
  const key = `${group}.${value}` as const

  return hasMessage(t, key) ? t(key) : value
}

/** A key's permissions as checkboxes, laid out like the email preferences' digest: "Select all"
 * (a dash when only some are ticked; a new key only), then each group's permissions under its name. A read that
 * a ticked permission comes with stays ticked. With `allowed`, only those can be ticked (a key's
 * permissions are only ever narrowed). */
export function PermissionTicks({
  options,
  ticked,
  onChange,
  allowed,
  disabled = false,
}: {
  options: PermissionOptions
  ticked: string[]
  onChange: (ticked: string[]) => void
  allowed?: string[]
  disabled?: boolean
}) {
  const t = useTranslations("api")
  const all = allowed ?? Object.values(options.permission_groups).flat()
  const locked = lockedReads(ticked, options.implied)
  const on = all.filter((item) => ticked.includes(item)).length

  function change(permission: string, checked: boolean) {
    onChange(
      checked
        ? tick(ticked, permission, options.implied)
        : ticked.filter((item) => item !== permission)
    )
  }

  return (
    <div className="space-y-4 rounded-2xl border p-4 sm:p-6">
      {/* Only for a new key: narrowing a key has nothing to select. */}
      {!allowed && (
        <label className={`${LABEL} gap-4`}>
          <Checkbox
            className={BIG}
            checked={on === all.length}
            indeterminate={on > 0 && on < all.length}
            disabled={disabled}
            onCheckedChange={(checked) => onChange(checked ? all : [])}
          />
          <span className="text-lg font-light">{t("selectAll")}</span>
        </label>
      )}
      {/* Lined up with "Select all"'s text. */}
      <div className={allowed ? "space-y-4" : "space-y-4 ps-11"}>
        {Object.entries(options.permission_groups).map(([group, items]) => (
          <fieldset key={group} className="space-y-2">
            <legend className="text-base">
              {named(t, "permissionGroups", group)}
            </legend>
            {/* Two columns on phones; a group's only permission takes the whole row. */}
            <div
              className={
                items.length === 1
                  ? "flex"
                  : "grid grid-cols-2 gap-x-6 gap-y-3 sm:flex sm:flex-wrap"
              }
            >
              {items.map((permission) => (
                <label
                  key={permission}
                  className={`${LABEL} gap-3 text-base font-light text-muted-foreground`}
                >
                  <Checkbox
                    className={SMALL}
                    checked={
                      ticked.includes(permission) || locked.has(permission)
                    }
                    disabled={
                      disabled ||
                      locked.has(permission) ||
                      !all.includes(permission)
                    }
                    onCheckedChange={(checked) => change(permission, checked)}
                  />
                  {named(t, "permissions", permission)}
                </label>
              ))}
            </div>
          </fieldset>
        ))}
      </div>
    </div>
  )
}

/** A key's permissions, one group a line: its name, then each permission as a small tag, all on
 * that line. */
export function PermissionTags({
  permissions,
  groups,
}: {
  permissions: string[]
  groups: Record<string, string[]>
}) {
  const t = useTranslations("api")

  return (
    <span
      className="grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-2"
      data-testid="key-permissions"
    >
      {permissionsByGroup(permissions, groups).map((entry) => (
        <Fragment key={entry.group}>
          <span className="text-sm text-muted-foreground">
            {named(t, "permissionGroups", entry.group)}
          </span>
          <span className="flex gap-1.5">
            {entry.permissions.map((item) => (
              <Badge
                key={item}
                variant="outline"
                className="h-6 px-2.5 text-xs font-light normal-case"
              >
                {named(t, "permissionLine", item)}
              </Badge>
            ))}
          </span>
        </Fragment>
      ))}
    </span>
  )
}

/** "Edit permissions" on a key's row, an icon like the web hooks' actions: its checkboxes, of
 * which only the ticked ones can be unticked; adding one means making a new key. */
export function EditPermissions({
  companyId,
  apiKey,
  options,
}: {
  companyId: string
  apiKey: ApiKey
  options: PermissionOptions
}) {
  const t = useTranslations("api")
  const common = useTranslations("common")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [ticked, setTicked] = useState(apiKey.permissions)
  const [saving, setSaving] = useState(false)
  const changed = ticked.length !== apiKey.permissions.length

  function changeOpen(next: boolean) {
    if (saving) {
      return
    }

    setOpen(next)
    setTicked(apiKey.permissions)
  }

  async function save() {
    setSaving(true)

    try {
      await apiFetch(`/v1/manage/keys/${apiKey.id}?company_id=${companyId}`, {
        method: "PATCH",
        body: JSON.stringify({ permissions: ticked }),
      })
      setOpen(false)
      router.refresh()
    } catch (error) {
      toast.error(
        serviceRefusal(error, [409]) ??
          apiErrorMessage(error, t("permissionsFailed"))
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <IconButton label={t("editPermissions")} onClick={() => changeOpen(true)}>
        <ListChecksIcon className="size-6" />
      </IconButton>
      <Dialog open={open} onOpenChange={changeOpen}>
        <DialogContent showCloseButton={false} className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>{t("editPermissions")}</DialogTitle>
            <DialogDescription>
              {t.rich("editPermissionsText", { name: apiKey.name, ...bdi })}
            </DialogDescription>
          </DialogHeader>
          <PermissionTicks
            options={options}
            ticked={ticked}
            onChange={setTicked}
            allowed={apiKey.permissions}
            disabled={saving}
          />
          <DialogFooter>
            <DialogClose
              render={
                <Button
                  variant="outline"
                  className="h-10 px-5 text-base"
                  disabled={saving}
                />
              }
            >
              {common("cancel")}
            </DialogClose>
            <Button
              className="h-10 px-5 text-base"
              disabled={saving || !changed || !ticked.length}
              onClick={save}
            >
              {common("save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
