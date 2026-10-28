import { hubArticleRoute } from "@/components/content/content-routes"

/** One page of content/guides, under its hub. */
const route = hubArticleRoute("guides")

export const generateMetadata = route.generateMetadata

export default route.Page
