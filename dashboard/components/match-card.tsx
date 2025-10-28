"use client"

import { Heart, MapPin, Calendar, Users } from "lucide-react"

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

interface MatchCardProps {
  match: Match
  rank: number
  isTop?: boolean
}

export default function MatchCard({ match, rank, isTop }: MatchCardProps) {
  return (
    <div
      className={`group relative rounded-lg border transition-smooth overflow-hidden ${
        isTop
          ? "border-accent/50 bg-card shadow-lg shadow-accent/10 hover:shadow-xl hover:shadow-accent/20"
          : "border-border bg-card/50 hover:bg-card hover:border-accent/30"
      }`}
    >
      {/* Rank Badge */}
      <div className="absolute top-3 right-3 z-10">
        <div
          className={`px-3 py-1 rounded-full text-xs font-semibold transition-smooth ${
            isTop
              ? "bg-accent/20 text-accent border border-accent/30"
              : "bg-muted/50 text-muted-foreground border border-border"
          }`}
        >
          #{rank} Match
        </div>
      </div>

      {/* Content */}
      <div className="p-5 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-foreground">User {match._id.slice(0, 8)}</h3>
            <p className="text-sm text-muted-foreground mt-1">ID: {match._id}</p>
          </div>
          <Heart
            className={`w-5 h-5 transition-smooth ${
              isTop ? "text-accent fill-accent" : "text-muted-foreground hover:text-accent"
            }`}
          />
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="w-4 h-4 text-accent/60" />
            <span className="text-foreground/80">{match.Age} years</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Users className="w-4 h-4 text-accent/60" />
            <span className="text-foreground/80">{match.Gender}</span>
          </div>
          {match.State && (
            <div className="flex items-center gap-2 text-sm col-span-2">
              <MapPin className="w-4 h-4 text-accent/60" />
              <span className="text-foreground/80">{match.State}</span>
            </div>
          )}
        </div>

        {/* Details */}
        <div className="space-y-2 pt-2 border-t border-border/50">
          {match.Caste && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Caste:</span>
              <span className="text-foreground/80 font-medium">{match.Caste}</span>
            </div>
          )}
          {match.Sect && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Sect:</span>
              <span className="text-foreground/80 font-medium">{match.Sect}</span>
            </div>
          )}
          {match.Marital_Status && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Status:</span>
              <span className="text-foreground/80 font-medium">{match.Marital_Status}</span>
            </div>
          )}
        </div>

        {/* Content Snippet */}
        {match.content && (
          <div className="p-3 rounded-lg bg-muted/20 border border-border/50">
            <p className="text-xs text-muted-foreground line-clamp-2">{match.content}</p>
          </div>
        )}

        {/* View Profile Button */}
        <button className="w-full py-2 px-3 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-medium text-sm transition-smooth border border-accent/20 hover:border-accent/40">
          View Profile
        </button>
      </div>
    </div>
  )
}
