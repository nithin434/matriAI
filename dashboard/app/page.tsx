"use client"

import { useState, useEffect } from "react"
import { Heart, Search, Loader2, AlertCircle, Users } from "lucide-react"
import SearchPreferencesForm from "@/components/search-preferences-form"
import MatchCard from "@/components/match-card"
import AIReviewPanel from "@/components/ai-review-panel"
import CandidatesList from "@/components/candidates-list"
import HealthBadge from "@/components/health-badge"

const API_BASE_URL = "http://localhost:3000"

interface Match {
  _id: string
  Age: number
  Gender: string
  Caste?: string
  Sect?: string
  State?: string
  Marital_Status?: string
  content?: string
}

interface SearchParams {
  gender?: string
  same_gender?: boolean
  age_range?: [number, number]
  caste?: string
  sect?: string
  marital_status?: string
  state?: string
  preference?: string
  user_id?: string
  age_tolerance?: number
}

export default function Home() {
  const [searchParams, setSearchParams] = useState<SearchParams>({})
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCandidates, setTotalCandidates] = useState(0)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`http://localhost:3000/health`)
        if (!response.ok) {
          console.warn("[v0] API health check failed")
        }
      } catch (err) {
        console.warn("[v0] Cannot connect to API at", API_BASE_URL)
      }
    }
    checkHealth()
  }, [])

  const handleSearch = async (params: SearchParams) => {
    setSearchParams(params)
    setLoading(true)
    setError(null)

    try {
      const queryParams = new URLSearchParams()

      // Add optional parameters only if they have values
      if (params.preference) queryParams.append("query", params.preference)
      if (params.user_id) queryParams.append("user_id", params.user_id)
      if (params.gender) queryParams.append("gender", params.gender)
      if (params.same_gender) queryParams.append("same_gender", "true")
      if (params.caste) queryParams.append("caste", params.caste)
      if (params.sect) queryParams.append("sect", params.sect)
      if (params.marital_status) queryParams.append("marital_status", params.marital_status)
      if (params.state) queryParams.append("state", params.state)
      if (params.age_tolerance !== undefined) queryParams.append("age_tolerance", params.age_tolerance.toString())

      // Add age range only if both values are provided
      if (params.age_range) {
        queryParams.append("min_age", params.age_range[0].toString())
        queryParams.append("max_age", params.age_range[1].toString())
      }

      queryParams.append("top_k", "10")

      const url = `${API_BASE_URL}/match?${queryParams.toString()}`
      console.log("[v0] Fetching matches from:", url)

      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `API error: ${response.status}`)
      }

      const data = await response.json()
      console.log("[v0] Matches received:", data.results?.length || 0)
      setMatches(data.results || [])
      setTotalCandidates(data.candidates || 0)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred while fetching matches"
      console.error("[v0] Search error:", errorMessage)
      setError(errorMessage)
      setMatches([])
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setSearchParams({})
    setMatches([])
    setError(null)
  }

  const topMatches = matches.slice(0, 2)
  const allCandidates = matches.slice(0, 10)

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md transition-smooth">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-accent/10 border border-accent/20">
              <Heart className="w-5 h-5 text-accent" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">MatriAI</h1>
          </div>
          <HealthBadge apiUrl={API_BASE_URL} />
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Sidebar - Search Preferences */}
        <aside className="w-80 border-r border-border bg-card/50 overflow-y-auto">
          <SearchPreferencesForm onSearch={handleSearch} onClear={handleClear} apiUrl={API_BASE_URL} />
        </aside>

        {/* Center - Match Results */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Error State */}
            {error && (
              <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive animate-fadeInUp">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex flex-col items-center justify-center py-16 gap-4">
                <div className="relative w-12 h-12">
                  <Loader2 className="w-12 h-12 text-accent animate-spin" />
                </div>
                <p className="text-muted-foreground">Finding your perfect matches...</p>
              </div>
            )}

            {/* Empty State */}
            {!loading && matches.length === 0 && !error && (
              <div className="flex flex-col items-center justify-center py-16 gap-4">
                <div className="w-16 h-16 rounded-full bg-muted/30 flex items-center justify-center">
                  <Users className="w-8 h-8 text-muted-foreground" />
                </div>
                <div className="text-center">
                  <p className="text-lg font-medium">No matches yet</p>
                  <p className="text-sm text-muted-foreground">Adjust your preferences to find compatible matches</p>
                </div>
              </div>
            )}

            {/* Match Results */}
            {!loading && topMatches.length > 0 && (
              <>
                {/* Top Matches Comparison */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Search className="w-5 h-5 text-accent" />
                    <h2 className="text-lg font-semibold">Top Matches</h2>
                    <span className="text-sm text-muted-foreground">({totalCandidates} candidates)</span>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    {topMatches.map((match, idx) => (
                      <MatchCard key={match._id} match={match} rank={idx + 1} isTop={idx === 0} />
                    ))}
                  </div>
                </div>

                {/* AI Review Panel */}
                {topMatches.length > 0 && (
                  <AIReviewPanel match1={topMatches[0]} match2={topMatches[1]} userPreferences={searchParams} />
                )}
              </>
            )}
          </div>
        </main>

        {/* Right Sidebar - Candidates List */}
        {!loading && matches.length > 0 && (
          <aside className="w-72 border-l border-border bg-card/50 overflow-y-auto">
            <CandidatesList candidates={allCandidates} />
          </aside>
        )}
      </div>
    </div>
  )
}
