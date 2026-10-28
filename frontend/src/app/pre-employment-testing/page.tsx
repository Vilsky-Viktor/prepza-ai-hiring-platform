import { categoryRoute } from "@/components/content/content-routes"

/** A category page (content/pages/pre-employment-testing.md). */
const route = categoryRoute("pre-employment-testing", "preEmploymentTesting")

export const generateMetadata = route.generateMetadata

export default route.Page
