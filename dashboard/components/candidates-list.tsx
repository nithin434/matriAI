"use client"

import { Users, Filter } from "lucide-react"

interface Match {
  _id: string
  Age: number
  Gender: string
  State?: string
}

interface CandidatesListProps {
  candidates: Match[]
}

export default function CandidatesList({ candidates }: CandidatesListProps) {
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-10 p-4 border-b border-border bg-card/80 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold flex items-center gap-2">
            <Users className="w-4 h-4 text-accent" />
            Candidates
          </h3>
          <span className="text-xs bg-accent/10 text-accent px-2 py-1 rounded-full font-medium">
            {candidates.length}
          </span>
        </div>
        <button className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-muted/30 hover:bg-muted/50 text-sm text-foreground/80 transition-smooth border border-border/50">
          <Filter className="w-4 h-4" />
          Quick Filters
        </button>
      </div>

      {/* Candidates List */}
      <div className="flex-1 overflow-y-auto space-y-2 p-4">
        {candidates.map((candidate, idx) => (
          <div
            key={candidate._id}
            className="group p-3 rounded-lg border border-border/50 bg-card/30 hover:bg-card/60 hover:border-accent/30 transition-smooth cursor-pointer"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-sm font-medium text-foreground">#{idx + 1}</p>
                <p className="text-xs text-muted-foreground mt-0.5">ID: {candidate._id.slice(0, 6)}</p>
              </div>
              <span className="text-xs bg-accent/10 text-accent px-2 py-1 rounded font-medium">{candidate.Age}</span>
            </div>
            <div className="space-y-1 text-xs text-foreground/70">
              <p>{candidate.Gender}</p>
              {candidate.State && <p>{candidate.State}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
