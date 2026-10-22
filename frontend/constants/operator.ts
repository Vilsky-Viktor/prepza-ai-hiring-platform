// The company that runs prepza: the site's footer, contact page and structured data name it. Mirrors
// OPERATOR in packages/common/src/prepza_common/constants.py (tests/constants/operator.test.ts
// keeps them equal), which the legal texts and the emails' footer use.
export const OPERATOR = {
  name: "Arcolabs OÜ",
  registryCode: "17587452",
  address: "Sepapaja tn 6, 15551 Tallinn, Harju maakond, Estonia",
  email: "hello@prepza.ai",
}

// OPERATOR's address in its parts, for structured data's PostalAddress
// (tests/constants/operator.test.ts keeps them equal to the one line).
export const OPERATOR_POSTAL_ADDRESS = {
  streetAddress: "Sepapaja tn 6",
  postalCode: "15551",
  addressLocality: "Tallinn",
  addressRegion: "Harju maakond",
  addressCountry: "EE",
}
