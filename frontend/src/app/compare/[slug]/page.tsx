import { hubArticleRoute } from "@/components/content/content-routes"

/** One page of content/compare, under its hub. */
const route = hubArticleRoute("compare")

export const generateMetadata = route.generateMetadata

export default route.Page
