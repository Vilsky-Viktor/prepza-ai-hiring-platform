"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import { DescriptionBox } from "@/components/description-box"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { Generation } from "@/types/generation"

/** Starts a template from a role description; its review and progress follow on /generate. */
export function NewTemplate() {
  const t = useTranslations("superadmin")
  const router = useRouter()

  async function create(text: string, generateIn: string) {
    try {
      const generation = await apiFetch<Generation>(
        "/generate/superadmin/templates",
        {
          method: "POST",
          body: JSON.stringify({ text, generate_in: generateIn }),
        }
      )
      router.push(`/generate/${generation.id}?next=/superadmin/templates`)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("createFailed")))
    }
  }

  return (
    <DescriptionBox
      placeholder={t("placeholder")}
      label={t("description")}
      submitLabel={t("create")}
      onSubmit={create}
    />
  )
}
