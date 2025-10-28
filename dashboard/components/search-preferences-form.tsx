"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { RotateCcw, Loader2 } from "lucide-react"

interface SearchPreferencesFormProps {
  onSearch: (params: any) => void
  onClear: () => void
  apiUrl: string
}

export default function SearchPreferencesForm({ onSearch, onClear, apiUrl }: SearchPreferencesFormProps) {
  const [formData, setFormData] = useState({
    gender: "Male",
    same_gender: false,
    min_age: 22,
    max_age: 32,
    caste: "",
    sect: "",
    marital_status: "",
    state: "",
    preference: "",
    user_id: "",
    age_tolerance: 5,
  })

  const [showRegister, setShowRegister] = useState(false)
  const [registering, setRegistering] = useState(false)
  const [registerData, setRegisterData] = useState({
    age: 28,
    gender: "Male",
    marital_status: "Never Married",
    caste: "Brahmin",
    sect: "Iyer",
    state: "Tamil Nadu",
    about: "",
    partner_preference: "",
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    }))
  }

  const handleRegisterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setRegisterData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleRegisterUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setRegistering(true)

    try {
      const payload = {
        Age: Number.parseInt(registerData.age),
        Gender: registerData.gender,
        Marital_Status: registerData.marital_status,
        Caste: registerData.caste,
        Sect: registerData.sect,
        State: registerData.state,
        About: registerData.about,
        Partner_Preference: registerData.partner_preference,
      }

      console.log("[v0] Registering user with payload:", payload)

      const response = await fetch(`${apiUrl}/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Registration failed: ${response.status}`)
      }

      const data = await response.json()
      console.log("[v0] User registered successfully with ID:", data.user_id)

      localStorage.setItem("matriAI_user_id", data.user_id)
      setFormData((prev) => ({
        ...prev,
        user_id: data.user_id,
      }))
      setShowRegister(false)
      alert(
        `User registered successfully!\nID: ${data.user_id}\n\nYour ID has been saved. You can now search for matches.`,
      )
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Registration failed"
      console.error("[v0] Registration error:", errorMessage)
      alert(errorMessage)
    } finally {
      setRegistering(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch({
      gender: formData.gender,
      same_gender: formData.same_gender,
      age_range: [formData.min_age, formData.max_age],
      caste: formData.caste || undefined,
      sect: formData.sect || undefined,
      marital_status: formData.marital_status || undefined,
      state: formData.state || undefined,
      preference: formData.preference || undefined,
      user_id: formData.user_id || undefined,
      age_tolerance: formData.age_tolerance,
    })
  }

  const handleClearForm = () => {
    setFormData({
      gender: "Male",
      same_gender: false,
      min_age: 22,
      max_age: 32,
      caste: "",
      sect: "",
      marital_status: "",
      state: "",
      preference: "",
      user_id: "",
      age_tolerance: 5,
    })
    onClear()
  }

  if (showRegister) {
    return (
      <form onSubmit={handleRegisterUser} className="p-6 space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-accent rounded-full"></span>
            Register Profile
          </h3>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">Age</label>
          <Input type="number" name="age" value={registerData.age} onChange={handleRegisterChange} min="18" max="80" />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">Gender</label>
          <select
            name="gender"
            value={registerData.gender}
            onChange={handleRegisterChange}
            className="w-full px-3 py-2 rounded-md bg-input border border-border text-foreground transition-smooth focus:outline-none focus:ring-2 focus:ring-accent/50"
          >
            <option>Male</option>
            <option>Female</option>
            <option>Other</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">Marital Status</label>
          <select
            name="marital_status"
            value={registerData.marital_status}
            onChange={handleRegisterChange}
            className="w-full px-3 py-2 rounded-md bg-input border border-border text-foreground transition-smooth focus:outline-none focus:ring-2 focus:ring-accent/50"
          >
            <option>Never Married</option>
            <option>Divorced</option>
            <option>Widowed</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">Caste</label>
          <Input type="text" name="caste" value={registerData.caste} onChange={handleRegisterChange} />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">Sect</label>
          <Input type="text" name="sect" value={registerData.sect} onChange={handleRegisterChange} />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">State</label>
          <Input type="text" name="state" value={registerData.state} onChange={handleRegisterChange} />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">About You</label>
          <Textarea
            name="about"
            value={registerData.about}
            onChange={handleRegisterChange}
            placeholder="Tell us about yourself..."
            className="min-h-20 resize-none"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">Partner Preference</label>
          <Textarea
            name="partner_preference"
            value={registerData.partner_preference}
            onChange={handleRegisterChange}
            placeholder="What are you looking for in a partner?"
            className="min-h-20 resize-none"
          />
        </div>

        <div className="flex gap-2 pt-4">
          <Button
            type="submit"
            disabled={registering}
            className="flex-1 bg-accent hover:bg-accent/90 text-accent-foreground font-medium transition-smooth"
          >
            {registering ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Registering...
              </>
            ) : (
              "Register"
            )}
          </Button>
          <Button
            type="button"
            onClick={() => setShowRegister(false)}
            variant="outline"
            className="flex-1 border-border hover:bg-muted/50 transition-smooth bg-transparent"
          >
            Back
          </Button>
        </div>
      </form>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="p-6 space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="w-1 h-6 bg-accent rounded-full"></span>
          Search Preferences
        </h3>
      </div>

      {/* Gender */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground/80">Your Gender</label>
        <select
          name="gender"
          value={formData.gender}
          onChange={handleChange}
          className="w-full px-3 py-2 rounded-md bg-input border border-border text-foreground transition-smooth focus:outline-none focus:ring-2 focus:ring-accent/50"
        >
          <option>Male</option>
          <option>Female</option>
          <option>Other</option>
        </select>
      </div>

      {/* Same Gender Toggle */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50">
        <label className="text-sm font-medium">Match same gender</label>
        <input
          type="checkbox"
          name="same_gender"
          checked={formData.same_gender}
          onChange={handleChange}
          className="w-4 h-4 rounded cursor-pointer"
        />
      </div>

      {/* Age Range */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-foreground/80">Age Range</label>
        <div className="flex gap-2">
          <Input
            type="number"
            name="min_age"
            value={formData.min_age}
            onChange={handleChange}
            min="18"
            max="80"
            placeholder="Min"
            className="flex-1"
          />
          <Input
            type="number"
            name="max_age"
            value={formData.max_age}
            onChange={handleChange}
            min="18"
            max="80"
            placeholder="Max"
            className="flex-1"
          />
        </div>
        <p className="text-xs text-muted-foreground">
          {formData.min_age} - {formData.max_age} years
        </p>
      </div>

      {/* Age Tolerance */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground/80">Age Tolerance (±)</label>
        <Input
          type="number"
          name="age_tolerance"
          value={formData.age_tolerance}
          onChange={handleChange}
          min="0"
          max="20"
          placeholder="5"
        />
        <p className="text-xs text-muted-foreground">Used when searching with User ID</p>
      </div>

      {/* Caste */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground/80">Caste (optional)</label>
        <Input type="text" name="caste" value={formData.caste} onChange={handleChange} placeholder="e.g., Brahmin" />
      </div>

      {/* Sect */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground/80">Sect (optional)</label>
        <Input type="text" name="sect" value={formData.sect} onChange={handleChange} placeholder="e.g., Hindu" />
      </div>

      {/* Marital Status */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground/80">Marital Status (optional)</label>
        <select
          name="marital_status"
          value={formData.marital_status}
          onChange={handleChange}
          className="w-full px-3 py-2 rounded-md bg-input border border-border text-foreground transition-smooth focus:outline-none focus:ring-2 focus:ring-accent/50"
        >
          <option value="">Select...</option>
          <option>Never Married</option>
          <option>Divorced</option>
          <option>Widowed</option>
        </select>
      </div>

      {/* State */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground/80">State (optional)</label>
        <Input type="text" name="state" value={formData.state} onChange={handleChange} placeholder="e.g., Tamil Nadu" />
      </div>

      {/* Free-text Preference */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground/80">What you're looking for</label>
        <Textarea
          name="preference"
          value={formData.preference}
          onChange={handleChange}
          placeholder="Describe your ideal partner..."
          className="min-h-24 resize-none"
        />
      </div>

      {/* Requester User ID */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground/80">Your User ID (optional)</label>
        <Input
          type="text"
          name="user_id"
          value={formData.user_id}
          onChange={handleChange}
          placeholder="Auto-fill your preferences"
        />
        <p className="text-xs text-muted-foreground">Leave empty to use manual filters above</p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-4">
        <Button
          type="submit"
          className="flex-1 bg-accent hover:bg-accent/90 text-accent-foreground font-medium transition-smooth"
        >
          Find Matches
        </Button>
        <Button
          type="button"
          onClick={handleClearForm}
          variant="outline"
          className="flex-1 border-border hover:bg-muted/50 transition-smooth bg-transparent"
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          Clear
        </Button>
      </div>

      <button
        type="button"
        onClick={() => setShowRegister(true)}
        className="w-full py-2 px-3 rounded-lg bg-muted/30 hover:bg-muted/50 text-foreground/80 font-medium text-sm transition-smooth border border-border/50 hover:border-accent/30"
      >
        Create New Profile
      </button>
    </form>
  )
}
