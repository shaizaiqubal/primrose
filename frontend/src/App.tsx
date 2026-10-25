import { Bookmark, ChevronDown, ChevronUp, Search } from 'lucide-react'
import { useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { InboxScreen, SignInScreen, SignUpScreen, VerifyEmailScreen } from './AuthScreens'
import { SearchScreen } from './SearchScreen'
import { TopicDetailScreen, TopicsScreen } from './TopicScreens'
import { LibraryScreen, PaperScreen } from './PaperLibraryScreens'
import { EntitiesScreen, EntityPapersScreen } from './EntityScreens'
import { NotFoundScreen } from './NotFoundScreen'
import { UnauthorizedScreen } from './UnauthorizedScreen'
import { Button, Card, Chip, Field, Header } from './components/ui'
import './App.css'

const entityExamples = ['topic models', 'language model embeddings', 'weak supervision']

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SearchScreen />} />
      <Route path="/signin" element={<SignInScreen />} />
      <Route path="/signup" element={<SignUpScreen />} />
      <Route path="/inbox" element={<InboxScreen />} />
      <Route path="/verify-email" element={<VerifyEmailScreen />} />
      <Route path="/unauthorized" element={<UnauthorizedScreen />} />
      <Route path="/topics" element={<TopicsScreen />} />
      <Route path="/topics/:topicId" element={<TopicDetailScreen />} />
      <Route path="/entities" element={<EntitiesScreen />} />
      <Route path="/entities/:entityId/papers" element={<EntityPapersScreen />} />
      <Route path="/papers/:paperId" element={<PaperScreen />} />
      <Route path="/library" element={<LibraryScreen />} />
      {import.meta.env.DEV && <Route path="/foundation" element={<FoundationShowcase />} />}
      <Route path="*" element={<NotFoundScreen />} />
    </Routes>
  )
}

function FoundationShowcase() {
  const [selectedEntity, setSelectedEntity] = useState(entityExamples[0])

  return (
    <div className="app-shell">
      <Header authenticated={Boolean(localStorage.getItem('primrose-access-token'))} />
      <main className="showcase page-width">
        <div className="showcase__intro">
          <p className="eyebrow">Primrose / Foundation</p>
          <h1 className="display-title">A quieter way to explore research.</h1>
          <p className="showcase__lede">
            Shared interface pieces for long evenings with difficult papers.
          </p>
        </div>

        <section className="showcase-section" aria-labelledby="header-variants">
          <div className="showcase-section__heading">
            <span className="eyebrow">01</span>
            <h2 id="header-variants">Header</h2>
          </div>
          <p className="section-note">Logged in</p>
          <div className="header-sample">
            <Header authenticated activePath="/topics" />
          </div>
        </section>

        <div className="showcase-grid">
          <section className="showcase-section" aria-labelledby="buttons-heading">
            <div className="showcase-section__heading">
              <span className="eyebrow">02</span>
              <h2 id="buttons-heading">Buttons</h2>
            </div>
            <div className="sample-row">
              <Button variant="primary">Open paper</Button>
              <Button>Secondary action</Button>
              <Button variant="icon" aria-label="Save for later" title="Save for later">
                <Bookmark size={19} strokeWidth={1.8} />
              </Button>
              <Button variant="icon" aria-label="Show abstract" title="Show abstract">
                <ChevronDown size={19} strokeWidth={1.8} />
              </Button>
              <Button variant="icon" aria-label="Hide abstract" title="Hide abstract">
                <ChevronUp size={19} strokeWidth={1.8} />
              </Button>
            </div>
          </section>

          <section className="showcase-section" aria-labelledby="chips-heading">
            <div className="showcase-section__heading">
              <span className="eyebrow">03</span>
              <h2 id="chips-heading">Chips</h2>
            </div>
            <div className="sample-row sample-row--wrap">
              {entityExamples.map((entity) => (
                <Chip
                  key={entity}
                  selected={selectedEntity === entity}
                  onClick={() => setSelectedEntity(entity)}
                >
                  {entity}
                </Chip>
              ))}
            </div>
          </section>
        </div>

        <section className="showcase-section" aria-labelledby="cards-heading">
          <div className="showcase-section__heading">
            <span className="eyebrow">04</span>
            <h2 id="cards-heading">Cards</h2>
          </div>
          <Card className="paper-card">
            <p className="paper-card__meta">Research paper · 2022</p>
            <h3 className="paper-card__title">A considered place for a paper title</h3>
            <div className="sample-row">
              <Button variant="primary">Open paper</Button>
              <Button variant="icon" aria-label="Save for later" title="Save for later">
                <Bookmark size={19} strokeWidth={1.8} />
              </Button>
              <Button variant="icon" aria-label="Show abstract" title="Show abstract">
                <ChevronDown size={19} strokeWidth={1.8} />
              </Button>
            </div>
          </Card>
        </section>

        <section className="showcase-section" aria-labelledby="fields-heading">
          <div className="showcase-section__heading">
            <span className="eyebrow">05</span>
            <h2 id="fields-heading">Form fields</h2>
          </div>
          <div className="fields-sample">
            <Field label="Email" requirement="Required" type="email" placeholder="you@example.com" />
            <Field label="Paper title" requirement="Optional" placeholder="A paper title" />
            <label className="field">
              <span className="field__label">Abstract <span className="field__requirement">Optional</span></span>
              <textarea className="field__input field__textarea" placeholder="Paste the abstract" />
            </label>
            <div className="search-sample">
              <label className="visually-hidden" htmlFor="search-field">Search papers</label>
              <input id="search-field" className="search-sample__input" placeholder="Ask in your own words." />
              <Button variant="primary"><Search size={18} /> Search</Button>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}