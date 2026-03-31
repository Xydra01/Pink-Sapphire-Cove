import './App.css'
import { useCoveDragons } from './hooks/useCoveDragons'
import { ScrollImport } from './components/ScrollImport'
import { BatchDropOff } from './components/BatchDropOff'
import { GeodeGrid } from './components/GeodeGrid'
import { CoveGrid } from './components/CoveGrid'
import pinkSapphire from './assets/pink-sapphire.png'

function App() {
  const { data, isLoading, error } = useCoveDragons()

  return (
    <>
      <section id="center">
        <div className="hero">
          <img src={pinkSapphire} className="base" width="180" height="180" alt="Pink sapphire emblem" />
        </div>
        <div>
          <h1>Pink Sapphire Cove</h1>
          <p style={{ marginTop: 12 }}>
            {error ? (
              <strong style={{ color: 'var(--garnet-alert)' }}>API offline</strong>
            ) : isLoading ? (
              'Checking the Cove…'
            ) : (
              <>
                Cove has <strong>{data?.length ?? 0}</strong> dragons
              </>
            )}
          </p>
          {error ? (
            <p style={{ marginTop: 8, opacity: 0.8, fontSize: 13 }}>
              Details: <code>{error.message}</code>
            </p>
          ) : null}
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
