import { getLocale, getTranslations } from "next-intl/server"

import { AccountData } from "@/features/settings/components/account-data"
import { AccountId } from "@/features/settings/components/account-id"
import { EmailPreferencesSetting } from "@/components/common/email-preferences"
import { CurrencySetting } from "@/features/settings/components/currency-setting"
import { LanguageSetting } from "@/features/settings/components/language-setting"
import { SettingsSection } from "@/components/common/settings-section"
import type { Locale } from "@/config/i18n"
import { currencyPath } from "@/lib/catalog"
import { serverFetch } from "@/lib/server-api"
import type { CurrencyChoice } from "@/types/billing"
import type { EmailPreferences } from "@/types/emails"

export default async function GeneralSettingsPage() {
  const t = await getTranslations("settings")
  const locale = (await getLocale()) as Locale
  const [emails, currency] = await Promise.all([
    serverFetch<EmailPreferences>("/library/me/email-preferences"),
    serverFetch<CurrencyChoice>(await currencyPath()),
  ])

  return (
    <>
      {/* Side by side on desktop, one under the other otherwise. */}
      <div className="grid gap-8 lg:grid-cols-2">
        <SettingsSection title={t("language")} description={t("languageNote")}>
          <LanguageSetting current={locale} />
        </SettingsSection>
        {currency && (
          <SettingsSection
            title={t("currency")}
            description={t("currencyNote")}
          >
            <CurrencySetting initial={currency} />
          </SettingsSection>
        )}
      </div>
      {emails && (
        <SettingsSection
          title={t("emails.title")}
          description={t("emails.note")}
        >
          <EmailPreferencesSetting initial={emails} />
        </SettingsSection>
      )}
      {/* Side by side on desktop, one under the other otherwise. */}
      <div className="grid gap-8 lg:grid-cols-2">
        <SettingsSection title={t("account")} description={t("accountNote")}>
          <AccountId />
        </SettingsSection>
        <SettingsSection title={t("yourData")} description={t("yourDataNote")}>
          <AccountData />
        </SettingsSection>
      </div>
    </>
  )
}
