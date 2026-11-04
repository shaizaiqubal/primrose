import type { ReactNode } from 'react'
import { FileText } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Document } from '../api.ts'
import { PaperActions, PaperCard } from './PaperCard'

export function PaperResultsLayout({
  documents,
  label,
  selectedPaperId,
  onSelect,
  footer,
  browseLinks = false,
}: {
  documents: Document[]
  label: string
  selectedPaperId: number | null
  onSelect: (id: number) => void
  footer?: ReactNode
  browseLinks?: boolean
}) {
  const selectedPaper = documents.find((paper) => paper.id === selectedPaperId) ?? null
  return (
    <section className="search-results search-results--master-detail" aria-label="Paper results">
      <div className="search-results__header">
        <span>{label}</span>
        {browseLinks && <nav aria-label="Browse Primrose"><span>Prefer to browse?</span> <Link to="/topics">Topics</Link> <span>or</span> <Link to="/entities">entities</Link></nav>}
      </div>
      <div className="search-results__layout">
        <div className="search-results__list">
          {documents.map((document) => <PaperCard compact document={document} key={document.id} onSelect={() => onSelect(document.id)} selected={selectedPaperId === document.id} />)}
          {footer}
        </div>
        <aside aria-label="Paper preview" className="search-detail">
          {selectedPaper ? <>
            <p className="search-detail__meta">{selectedPaper.authors || 'Paper'}{selectedPaper.year_published ? `, ${selectedPaper.year_published}` : ''}</p>
            <h2>{selectedPaper.title}</h2>
            <div className="search-detail__actions"><PaperActions document={selectedPaper} /></div>
            <p className="search-detail__label">Abstract</p>
            <p className="search-detail__abstract">{selectedPaper.abstract || 'No abstract available.'}</p>
          </> : <div className="search-detail__empty"><FileText aria-hidden="true" size={34} strokeWidth={1.5} /><h2>Select a paper to preview it</h2><p>Its abstract and details will show here.</p></div>}
        </aside>
      </div>
    </section>
  )
}
