import { categoryRoute } from "@/features/content/components/content-routes"

/** A category page (content/pages/ai-interviews.md). */
const route = categoryRoute("ai-interviews", "aiInterviews")

export const generateMetadata = route.generateMetadata

export default route.Page
