import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'
import { useCoveDragons } from './hooks/useCoveDragons'
import { ScrollImport } from './components/ScrollImport'
import { BatchDropOff } from './components/BatchDropOff'
import { GeodeGrid } from './components/GeodeGrid'
import { CoveGrid } from './components/CoveGrid'

function App() {
  const { data, isLoading, error } = useCoveDragons()

  return (
    <>
      <section id="center">
        <div className="hero">
          <img src={heroImg} className="base" width="170" height="179" alt="" />
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div>
        <div>
          <h1>Pink Sapphire Cove</h1>
          <p style={{ marginTop: 12 }}>
            API status:{' '}
            {error ? (
              <strong style={{ color: 'var(--garnet-alert)' }}>{error.message}</strong>
            ) : isLoading ? (
              'Loading…'
            ) : (
              <>
                Cove has <strong>{data?.length ?? 0}</strong> dragons
              </>
            )}
          </p>
        </div>
      </section>

      <div className="ticks"></div>

      <ScrollImport />

      <BatchDropOff />

      <section className="grid-section grid-section--geode">
        <h2 className="grid-section__title">
          <span>The Geode</span>
        </h2>
        <GeodeGrid />
      </section>

      <section className="grid-section">
        <h2 className="grid-section__title">
          <span>The Cove</span>
        </h2>
        <CoveGrid />
      </section>

      <div className="ticks"></div>
      <section id="spacer"></section>
    </>
  )
}

export default App
