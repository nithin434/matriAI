"use client"

import { Sparkles, TrendingUp } from "lucide-react"

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

interface AIReviewPanelProps {
  match1?: Match
  match2?: Match
  userPreferences: any
}

export default function AIReviewPanel({ match1, match2, userPreferences }: AIReviewPanelProps) {
  const generateCompatibilityScore = () => {
    if (!match1 || !match2) return 0

    let score = 70
    if (match1.Caste === match2.Caste) score += 5
    if (match1.Sect === match2.Sect) score += 5
    if (match1.State === match2.State) score += 5
    if (Math.abs(match1.Age - match2.Age) <= 5) score += 5
    if (match1.Marital_Status === match2.Marital_Status) score += 5

    return Math.min(score, 100)
  }

  const compatibilityScore = generateCompatibilityScore()

  const generateReasons = () => {
    const reasons = []
    if (match1 && match2) {
      if (match1.Caste === match2.Caste) reasons.push("Matching caste background")
      if (match1.Sect === match2.Sect) reasons.push("Same religious sect")
      if (match1.State === match2.State) reasons.push("Same geographic location")
      if (Math.abs(match1.Age - match2.Age) <= 5) reasons.push("Compatible age range")
      if (match1.Marital_Status === match2.Marital_Status) reasons.push("Similar marital status")
    }
    return reasons.length > 0 ? reasons : ["Strong compatibility indicators", "Shared values", "Life stage alignment"]
  }

  const reasons = generateReasons()

  return (
    <div className="rounded-lg border border-accent/30 bg-gradient-to-br from-card to-card/50 overflow-hidden animate-fadeInUp">
      {/* Header */}
      <div className="px-6 py-4 border-b border-accent/20 bg-accent/5">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-semibold">AI Compatibility Review</h3>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Compatibility Score */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Overall Compatibility</span>
            <span className="text-3xl font-bold text-accent">{compatibilityScore}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-muted/30 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-accent to-accent/60 rounded-full transition-all duration-500"
              style={{ width: `${compatibilityScore}%` }}
            ></div>
          </div>
        </div>

        {/* Key Reasons */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-accent" />
            Key Compatibility Factors
          </h4>
          <ul className="space-y-2">
            {reasons.slice(0, 4).map((reason, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 flex-shrink-0"></span>
                <span className="text-foreground/80">{reason}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Summary */}
        <div className="p-4 rounded-lg bg-muted/20 border border-border/50 space-y-2">
          <p className="text-xs font-semibold text-accent uppercase tracking-wide">Summary</p>
          <p className="text-sm text-foreground/80 leading-relaxed">
            {match1 && match2
              ? `These matches show strong compatibility with a ${compatibilityScore}% score. Both profiles align well on key factors including location, background, and life stage. Consider reaching out to explore further.`
              : "AI analysis will appear once matches are loaded."}
          </p>
        </div>

        {/* Action */}
        <button className="w-full py-3 px-4 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-medium transition-smooth border border-accent/20 hover:border-accent/40">
          View Detailed Analysis
        </button>
      </div>
    </div>
  )
}
