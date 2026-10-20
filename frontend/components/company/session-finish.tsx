import { useTranslations } from "next-intl"

import { RoundFooter } from "@/components/session/round-footer"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

/** Finish, and Next once an option is picked. */
export function SessionFooter({
  finishing,
  sending,
  picked,
  onFinish,
  onNext,
}: {
  finishing: boolean
  sending: boolean
  picked: boolean
  onFinish: () => void
  onNext: () => void
}) {
  const t = useTranslations("session")
  const rounds = useTranslations("rounds")

  return (
    <RoundFooter>
      <Button
        variant="ghost"
        className="h-12 px-6 text-base"
        disabled={finishing || sending}
        onClick={onFinish}
        data-testid="finish-interview"
      >
        {finishing ? rounds("finishing") : t("finish")}
      </Button>
      <div className="flex items-center gap-3">
        {picked && (
          // Focus stays on the pick, so it can still be changed; Next is the following stop.
          <Button
            className="h-12 px-6 text-base"
            disabled={sending}
            onClick={onNext}
            data-testid="next-question"
          >
            {rounds("next")}
          </Button>
        )}
      </div>
    </RoundFooter>
  )
}

/** Asks before finishing: it ends every section, and says how many questions stay unanswered
 * (unscored). It can't be closed while finishing. */
export function FinishDialog({
  open,
  finishing,
  sections,
  unanswered,
  onClose,
  onFinish,
}: {
  open: boolean
  finishing: boolean
  sections: number
  unanswered: number | null
  onClose: () => void
  onFinish: () => void
}) {
  const t = useTranslations("session")
  const rounds = useTranslations("rounds")
  const common = useTranslations("common")

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next && !finishing) {
          onClose()
        }
      }}
    >
      <DialogContent showCloseButton={false}>
        <DialogHeader className="gap-4">
          <DialogTitle className="no-dot mb-2">{t("finishTitle")}</DialogTitle>
          <DialogDescription>
            {sections > 1 ? t("endsAll", { count: sections }) : t("endsOne")}
            {unanswered !== null && ` ${t("unscored", { count: unanswered })}`}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={finishing}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            className="h-10 px-5 text-base"
            disabled={finishing}
            onClick={onFinish}
          >
            {finishing ? rounds("finishing") : rounds("finish")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
