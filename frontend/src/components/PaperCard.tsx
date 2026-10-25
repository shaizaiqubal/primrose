import { useState } from 'react'
import { Bookmark, ChevronDown, ChevronUp } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { addBookmark, removeBookmark, type Document } from '../api.ts'
import { Button, Card } from './ui'

function authorSummary(authors: string | null, year: number | null) {
  const names = authors?.split(',').map((name) => name.trim()).filter(Boolean) ?? []
  const byline = names.length > 3 ? `${names.slice(0, 2).join(', ')} and ${names.length - 2} others` : names.join(', ')
  return [byline, year].filter(Boolean).join(', ')
}

export function PaperCard({ document, saved = false }: { document: Document; saved?: boolean }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [expanded, setExpanded] = useState(false)
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

  return (
    <Card className="paper-card">
      <p className="paper-card__meta">{authorSummary(document.authors, document.year_published) || 'Paper'}</p>
      <h2 className="paper-card__title"><Link to={`/papers/${document.id}`}>{document.title}</Link></h2>
      <div className="sample-row">
        <Link className="button button--primary" to={`/papers/${document.id}`}>Open paper</Link>
        <Button
          aria-label={isSaved ? 'Saved. Remove from saved' : 'Save for later'}
          disabled={saving}
          onClick={toggleBookmark}
          title={isSaved ? 'Saved. Remove from saved' : 'Save for later'}
          variant="icon"
        >
          <Bookmark fill={isSaved ? 'currentColor' : 'none'} size={19} strokeWidth={1.8} />
        </Button>
        <Button
          aria-expanded={expanded}
          aria-label={expanded ? 'Hide abstract' : 'Show abstract'}
          onClick={() => setExpanded((current) => !current)}
          title={expanded ? 'Hide abstract' : 'Show abstract'}
          variant="icon"
        >
          {expanded ? <ChevronUp size={19} strokeWidth={1.8} /> : <ChevronDown size={19} strokeWidth={1.8} />}
        </Button>
      </div>
      {bookmarkError && <p className="paper-card__error" role="alert">{bookmarkError}</p>}
      {expanded && <p className="paper-card__abstract">{document.abstract}</p>}
    </Card>
  )
}