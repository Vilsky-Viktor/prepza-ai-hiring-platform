/** One block of a settings page: a title, a short note and its controls; `action`, when given,
 * sits on the right of all of it, centered vertically. The controls sit at the bottom, so two
 * blocks side by side, as tall as each other, line them up. */
export function SettingsSection({
  title,
  description,
  action,
  children,
}: {
  title: string
  description: string
  action?: React.ReactNode
  children?: React.ReactNode
}) {
  return (
    <section
      className={`flex gap-6 rounded-xl border p-6 ${action ? "items-center" : "items-start"}`}
    >
      {/* Its controls at the bottom, so blocks side by side line them up whatever their notes'
          length. */}
      <div className="flex min-w-0 flex-1 flex-col gap-4 self-stretch">
        <div className="space-y-1">
          <h2 className="text-lg font-medium">{title}</h2>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        {children && <div className="mt-auto">{children}</div>}
      </div>
      {action}
    </section>
  )
}
