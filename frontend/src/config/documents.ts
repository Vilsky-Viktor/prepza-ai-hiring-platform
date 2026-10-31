// The documents on the /documents page, in its order. scripts/documents/build.sh makes the files in
// public/documents from content/documents; their titles and descriptions are in messages
// ("docs.items"), and `online` is the page that shows the same text.
export const DOCUMENTS = [
  {
    key: "instructions",
    format: "PDF",
    href: "/documents/testee-instructions-for-companies.pdf",
  },
  {
    key: "notices",
    format: "DOCX",
    href: "/documents/testee-candidate-notice-templates.docx",
  },
  {
    key: "dpia",
    format: "DOCX",
    href: "/documents/testee-dpia-template.docx",
  },
  {
    key: "dpa",
    format: "PDF",
    href: "/documents/testee-data-processing-agreement.pdf",
    online: "/dpa",
  },
] as const
