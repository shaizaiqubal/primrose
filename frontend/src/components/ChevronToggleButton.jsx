import { ChevronDown } from "lucide-react"

export default function ChevronToggleButton({ expanded, onClick, ariaLabel, className = "" }) {
  return (
    <button
      type="button"
      className={`chevron-toggle-btn ${className}`.trim()}
      onClick={onClick}
      aria-label={ariaLabel}
      title={ariaLabel}
    >
      <ChevronDown
        className={`chevron-toggle-icon ${expanded ? "expanded" : ""}`.trim()}
        aria-hidden="true"
      />
    </button>
  )
}
