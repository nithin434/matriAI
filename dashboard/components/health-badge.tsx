"use client"

import { useEffect, useState } from "react"

interface HealthBadgeProps {
  apiUrl: string
}

export default function HealthBadge({ apiUrl }: HealthBadgeProps) {
  const [status, setStatus] = useState("checking")

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${apiUrl}/health`)
        if (response.ok) {
          setStatus("healthy")
        } else {
          setStatus("error")
        }
      } catch (err) {
        console.warn("[v0] Health check failed:", err)
        setStatus("error")
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [apiUrl])

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted/30 border border-border/50">
      <div
        className={`w-2 h-2 rounded-full ${status === "healthy" ? "bg-green-500 animate-pulse" : status === "checking" ? "bg-yellow-500 animate-pulse" : "bg-red-500"}`}
      ></div>
      <span className="text-xs font-medium text-muted-foreground capitalize">
        {status === "checking" ? "Checking..." : status === "healthy" ? "System Healthy" : "Offline"}
      </span>
    </div>
  )
}
