// The documents on the /documents page, in its order. scripts/documents/build.sh makes the files in
// public/documents from content/documents; their titles and descriptions are in messages
// ("docs.items"), and `online` is the page that shows the same text.
export const DOCUMENTS = [
  {
    key: "instructions",
    format: "PDF",
    href: "/documents/prepza-instructions-for-companies.pdf",
  },
  {
    key: "notices",
    format: "DOCX",
    href: "/documents/prepza-candidate-notice-templates.docx",
  },
  {
    key: "dpia",
    format: "DOCX",
    href: "/documents/prepza-dpia-template.docx",
  },
  {
    key: "dpa",
    format: "PDF",
    href: "/documents/prepza-data-processing-agreement.pdf",
    online: "/dpa",
  },
] as const
