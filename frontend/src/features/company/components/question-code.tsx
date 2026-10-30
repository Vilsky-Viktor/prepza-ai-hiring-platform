import { QuestionText } from "@/components/common/question-text"

/** A question's code examples, under its card on the interview screens (click and voice). On
 * phones the code runs the screen's full width, square-cornered, like the question's card. */
export function QuestionCode({ code }: { code: string }) {
  return (
    <div className="max-sm:-mx-6 max-sm:[&_[data-slot=code-editor]]:rounded-none max-sm:[&_[data-slot=code-editor]]:border-x-0">
      <QuestionText text={code} />
    </div>
  )
}
