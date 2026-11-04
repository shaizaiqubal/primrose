import { useState, type KeyboardEvent, type MouseEvent } from 'react'
import { Bookmark } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { addBookmark, removeBookmark, type Document } from '../api.ts'
import { Button, Card } from './ui'

function authorSummary(authors: string | null, year: number | null) {
  const names = authors?.split(',').map((name) => name.trim()).filter(Boolean) ?? []
  const byline = names.length > 3 ? `${names.slice(0, 2).join(', ')} and ${names.length - 2} others` : names.join(', ')
  return [byline, year].filter(Boolean).join(', ')
}

type PaperCardProps = {
  document: Document
  saved?: boolean
  compact?: boolean
  selected?: boolean
  onSelect?: () => void
}

export function PaperActions({ document, saved = false }: { document: Document; saved?: boolean }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [isSaved, setIsSaved] = useState(saved)
  const [bookmarkError, setBookmarkError] = useState('')
  const [saving, setSaving] = useState(false)

  async function toggleBookmark() {
    if (!localStorage.getItem('primrose-access-token')) {
      navigate('/unauthorized', { state: { returnTo: location.pathname } })
      return
    }
    setSaving(true)
    setBookmarkError('')
    try {
      if (isSaved) await removeBookmark(document.id)
      else await addBookmark(document.id)
      setIsSaved(!isSaved)
    } catch {
      setBookmarkError('We could not update this saved paper just now.')
    } finally {
      setSaving(false)
    }
  }

  return <div className="paper-actions">
    <Link className="button button--primary" to={`/papers/${document.id}`}>Open paper</Link>
    <Button
      aria-label={isSaved ? 'Saved. Remove from saved' : 'Save paper'}
      disabled={saving}
      onClick={toggleBookmark}
      title={isSaved ? 'Saved. Remove from saved' : 'Save paper'}
      variant="icon"
    >
      <Bookmark fill={isSaved ? 'currentColor' : 'none'} size={19} strokeWidth={1.8} />
    </Button>
    {bookmarkError && <p className="paper-card__error" role="alert">{bookmarkError}</p>}
  </div>
}

export function PaperCard({ document, saved = false, compact = true, selected = false, onSelect }: PaperCardProps) {
  function handleClick(event: MouseEvent<HTMLElement>) {
    if (onSelect && !(event.target as HTMLElement).closest('button, a')) onSelect()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (!onSelect || (event.key !== 'Enter' && event.key !== ' ')) return
    event.preventDefault()
    onSelect()
  }

  return (
    <Card
      aria-current={selected ? 'true' : undefined}
      aria-pressed={onSelect ? selected : undefined}
      className={`paper-card${compact ? ' paper-card--compact' : ''}${selected ? ' is-selected' : ''}`}
      onClick={onSelect ? handleClick : undefined}
      onKeyDown={onSelect ? handleKeyDown : undefined}
      aria-label={onSelect ? `Select ${document.title}` : undefined}
      role={onSelect ? 'button' : undefined}
      tabIndex={onSelect ? 0 : undefined}
    >
      <div className="paper-card__copy">
        <p className="paper-card__meta">{authorSummary(document.authors, document.year_published) || 'Paper'}</p>
        <h2 className="paper-card__title"><Link to={`/papers/${document.id}`}>{document.title}</Link></h2>
      </div>
      <PaperActions document={document} saved={saved} />
    </Card>
  )
}
