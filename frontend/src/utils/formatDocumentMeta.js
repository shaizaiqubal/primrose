function formatCategories(categories) {
  if (!categories) return ""
  if (Array.isArray(categories)) return categories.filter(Boolean).join(", ")
  return String(categories).trim()
}

export function formatDocumentMeta(doc) {
  const parts = []

  if (doc?.authors) parts.push(doc.authors)
  if (doc?.year_published) parts.push(String(doc.year_published))
  return parts.join(" · ")
}
