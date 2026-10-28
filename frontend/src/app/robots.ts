import type { MetadataRoute } from "next"

import { UNCRAWLED_PATHS } from "@/constants/seo"
import { siteUrl } from "@/lib/site"

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: UNCRAWLED_PATHS },
    sitemap: `${siteUrl()}/sitemap.xml`,
  }
}
