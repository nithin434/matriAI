export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)

  // Mock response - replace with actual API call to your FastAPI backend
  const mockResults = [
    {
      _id: "507f1f77bcf86cd799439011",
      Age: 28,
      Gender: "Female",
      Caste: "Brahmin",
      Sect: "Hindu",
      State: "California",
      Marital_Status: "Never Married",
      content: "Looking for a caring and ambitious partner who values family and personal growth.",
    },
    {
      _id: "507f1f77bcf86cd799439012",
      Age: 26,
      Gender: "Female",
      Caste: "Kshatriya",
      Sect: "Hindu",
      State: "Texas",
      Marital_Status: "Never Married",
      content: "Passionate about travel and cooking. Seeking someone with similar interests.",
    },
    {
      _id: "507f1f77bcf86cd799439013",
      Age: 29,
      Gender: "Female",
      Caste: "Brahmin",
      Sect: "Hindu",
      State: "New York",
      Marital_Status: "Never Married",
      content: "Professional woman interested in building a meaningful relationship.",
    },
  ]

  return Response.json({
    query: searchParams.get("query") || "looking for suitable partner",
    filters: Object.fromEntries(searchParams),
    candidates: 45,
    took_ms: 234,
    results: mockResults,
  })
}
