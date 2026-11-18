
import { useEffect, useState } from 'react'
import {
  LayoutDashboard,
  Upload,
  Map,
  BarChart3,
  Route,
  Activity,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Play,
  FileText,
  Clock,
  Menu,
  X,
  Database,
  Target,
  Zap,
  TrendingUp,
  ChevronRight,
  Server,
  LoaderCircle,
} from 'lucide-react'
import RouteMap from './components/RouteMap'

const API_BASE_URL = 'http://10.1.32.121:8000'

const navigation = [
  { name: 'Dashboard', icon: LayoutDashboard },
  { name: 'Upload Trip', icon: Upload },
  { name: 'Map Matching', icon: Map },
  { name: 'Results', icon: Route },
  { name: 'Model Performance', icon: BarChart3 },
]

const modelNames = [
  'Hidden Markov Model (HMM)',
  'Random Forest',
  'XGBoost',
  'Decision Tree',
  'K-Nearest Neighbors',
]

function StatCard({ title, value, subtitle, icon: Icon }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600">
          <Icon size={20} />
        </div>
      </div>
      <p className="mt-4 text-3xl font-bold text-slate-900">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
    </div>
  )
}

function App() {
  const [activePage, setActivePage] = useState('Dashboard')
  const [menuOpen, setMenuOpen] = useState(false)
  const [files, setFiles] = useState([])
  const [tripName, setTripName] = useState('')
  const [message, setMessage] = useState('')
  const [dragging, setDragging] = useState(false)

  // Backend and prediction states
  const [tripIds, setTripIds] = useState([])
  const [selectedTripId, setSelectedTripId] = useState('00000000')
  const [prediction, setPrediction] = useState(null)
  const [apiStatus, setApiStatus] = useState('Checking connection...')
  const [apiError, setApiError] = useState('')
  const [predictionLoading, setPredictionLoading] = useState(false)

  useEffect(() => {
    async function loadBackendData() {
      try {
        const healthResponse = await fetch(`${API_BASE_URL}/health`)
        if (!healthResponse.ok) {
          throw new Error('Backend health check failed.')
        }

        setApiStatus('Connected')

        const tripsResponse = await fetch(`${API_BASE_URL}/trips`)
        if (!tripsResponse.ok) {
          throw new Error('Could not load trips.')
        }

        const tripsData = await tripsResponse.json()
        const availableTrips = tripsData.trip_ids || []

        setTripIds(availableTrips)

        if (availableTrips.length > 0) {
          setSelectedTripId((current) =>
            availableTrips.includes(current) ? current : availableTrips[0]
          )
        }

        setApiError('')
      } catch (error) {
        setApiStatus('Disconnected')
        setApiError(
          `${error.message} Check that the backend is running and CORS is configured.`
        )
      }
    }

    loadBackendData()
  }, [])

  async function runPrediction() {
    if (!selectedTripId) {
      setApiError('Please select a trip first.')
      return
    }

    setPredictionLoading(true)
    setApiError('')
    setPrediction(null)

    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ trip_id: selectedTripId }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Prediction request failed.')
      }

      setPrediction(data)
    } catch (error) {
      setApiError(error.message)
    } finally {
      setPredictionLoading(false)
    }
  }

  const predictedSegments = (prediction?.predicted_arc_ids || []).reduce(
    (segments, arcId) => {
      const lastSegment = segments[segments.length - 1]

      if (lastSegment && lastSegment.arcId === arcId) {
        lastSegment.count += 1
      } else {
        segments.push({ arcId, count: 1 })
      }

      return segments
    },
    []
  )

  function handleFiles(selectedFiles) {
    const fileList = Array.from(selectedFiles || [])
    setFiles(fileList)
    setMessage(
      fileList.length
        ? `${fileList.length} file(s) selected successfully.`
        : ''
    )
  }

  function renderDashboard() {
    return (
      <div className="space-y-8">
        <div>
          <p className="text-sm font-semibold text-blue-600">OVERVIEW</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Dashboard
          </h1>
          <p className="mt-2 text-slate-500">
            Welcome to PathSnap — your map matching and route reconstruction
            platform.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Available Trips"
            value={tripIds.length}
            subtitle="Fetched from backend"
            icon={Route}
          />
          <StatCard
            title="Backend Status"
            value={apiStatus}
            subtitle="FastAPI connection"
            icon={Server}
          />
          <StatCard
            title="Selected Trip"
            value={selectedTripId}
            subtitle="Current trip ID"
            icon={Target}
          />
          <StatCard
            title="Prediction Status"
            value={prediction ? 'Completed' : 'Pending'}
            subtitle="Latest prediction"
            icon={Activity}
          />
        </div>

        {apiError && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {apiError}
          </div>
        )}

        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Recent Available Trips
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Live trips fetched from the FastAPI backend
              </p>
            </div>
            <button
              onClick={() => setActivePage('Results')}
              className="flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-800"
            >
              View results <ChevronRight size={16} />
            </button>
          </div>

          <div className="mt-5 divide-y divide-slate-100">
            {tripIds.length > 0 ? (
              tripIds.map((id) => (
                <button
                  key={id}
                  onClick={() => {
                    setSelectedTripId(id)
                    setActivePage('Results')
                  }}
                  className="flex w-full items-center justify-between py-4 text-left hover:bg-slate-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
                      <Route size={18} />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800">
                        Trip {id}
                      </p>
                      <p className="text-xs text-slate-500">
                        Available for prediction
                      </p>
                    </div>
                  </div>
                  <ChevronRight size={18} className="text-slate-400" />
                </button>
              ))
            ) : (
              <p className="py-6 text-sm text-slate-500">
                {apiStatus === 'Connected'
                  ? 'No trips were returned by the backend.'
                  : 'Waiting for backend connection...'}
              </p>
            )}
          </div>
        </div>
      </div>
    )
  }

  function renderUpload() {
    return (
      <div className="space-y-6">
        <div>
          <p className="text-sm font-semibold text-blue-600">DATA INPUT</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Upload Trip
          </h1>
          <p className="mt-2 text-slate-500">
            Select GPS trajectory files for your workflow.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <label className="mb-2 block text-sm font-semibold text-slate-700">
            Trip name
          </label>
          <input
            value={tripName}
            onChange={(event) => setTripName(event.target.value)}
            placeholder="Enter a trip name"
            className="mb-6 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-500"
          />

          <label
            onDragOver={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault()
              setDragging(false)
              handleFiles(event.dataTransfer.files)
            }}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 text-center transition ${
              dragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
            }`}
          >
            <div className="rounded-2xl bg-blue-50 p-4 text-blue-600">
              <Upload size={30} />
            </div>
            <p className="mt-4 font-semibold text-slate-800">
              Drop your GPS files here
            </p>
            <p className="mt-2 text-sm text-slate-500">
              or click to browse files
            </p>
            <p className="mt-2 text-xs text-slate-400">
              CSV, JSON or other trajectory data files
            </p>
            <input
              type="file"
              multiple
              accept=".csv,.json,.txt"
              className="hidden"
              onChange={(event) => handleFiles(event.target.files)}
            />
          </label>

          {files.length > 0 && (
            <div className="mt-5 space-y-2">
              <p className="font-semibold text-slate-700">Selected files</p>
              {files.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center gap-3 rounded-xl bg-slate-50 p-3"
                >
                  <FileText size={18} className="text-blue-600" />
                  <span className="text-sm text-slate-700">{file.name}</span>
                </div>
              ))}
            </div>
          )}

          {message && (
            <p className="mt-4 text-sm text-green-600">{message}</p>
          )}

          <p className="mt-5 text-xs text-slate-400">
            Note: File selection is currently local only; it does not upload
            files to the backend.
          </p>
        </div>
      </div>
    )
  }

  function renderMapMatching() {
    return (
      <div className="space-y-6">
        <div>
          <p className="text-sm font-semibold text-blue-600">ROUTE ANALYSIS</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Interactive Map
          </h1>
          <p className="mt-2 text-slate-500">
            Visualize GPS observations and an illustrative matched route.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-4 flex flex-wrap items-center gap-5 text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-3 w-3 rounded-full bg-orange-500" />
              GPS observations
            </span>
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-1 w-5 rounded bg-blue-600" />
              Illustrative matched route
            </span>
          </div>
          <RouteMap />
          <p className="mt-4 text-xs text-slate-400">
            Map currently displays illustrative Bengaluru coordinates, not
            coordinates returned by the prediction API.
          </p>
        </div>
      </div>
    )
  }

  function renderResults() {
    const accuracy =
      typeof prediction?.accuracy === 'number'
        ? `${(prediction.accuracy * 100).toFixed(2)}%`
        : '—'

    const continuity =
      typeof prediction?.route_continuity === 'number'
        ? `${(prediction.route_continuity * 100).toFixed(2)}%`
        : '—'

    const diagnostics = prediction?.diagnostics || {}

    return (
      <div className="space-y-6">
        <div>
          <p className="text-sm font-semibold text-blue-600">MODEL OUTPUT</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Prediction Results
          </h1>
          <p className="mt-2 text-slate-500">
            Run map matching predictions using the connected FastAPI backend.
          </p>
        </div>

        <div
          className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4 ${
            apiStatus === 'Connected'
              ? 'border-green-200 bg-green-50'
              : 'border-amber-200 bg-amber-50'
          }`}
        >
          <div className="flex items-center gap-3">
            {apiStatus === 'Connected' ? (
              <CheckCircle className="text-green-600" size={21} />
            ) : (
              <AlertCircle className="text-amber-600" size={21} />
            )}
            <div>
              <p className="font-semibold text-slate-800">
                Backend: {apiStatus}
              </p>
              <p className="text-xs text-slate-500">
                {API_BASE_URL}
              </p>
            </div>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <RefreshCw size={15} /> Refresh
          </button>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="font-bold text-slate-900">Select a trip</h2>
          <p className="mt-1 text-sm text-slate-500">
            Choose an available trip and request its predicted road segments.
          </p>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <select
              value={selectedTripId}
              onChange={(event) => {
                setSelectedTripId(event.target.value)
                setPrediction(null)
                setApiError('')
              }}
              className="min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-800 outline-none focus:border-blue-500"
            >
              {tripIds.length === 0 && (
                <option value="">No trips available</option>
              )}
              {tripIds.map((id) => (
                <option key={id} value={id}>
                  Trip {id}
                </option>
              ))}
            </select>

            <button
              onClick={runPrediction}
              disabled={
                predictionLoading ||
                !selectedTripId ||
                apiStatus !== 'Connected'
              }
              className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {predictionLoading ? (
                <>
                  <LoaderCircle className="animate-spin" size={18} />
                  Running...
                </>
              ) : (
                <>
                  <Play size={18} />
                  Run Prediction
                </>
              )}
            </button>
          </div>

          {apiError && (
            <div className="mt-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <span>{apiError}</span>
            </div>
          )}
        </div>

        {prediction && (
          <>
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
              <StatCard
                title="Prediction Accuracy"
                value={accuracy}
                subtitle="API-reported agreement metric"
                icon={Target}
              />
              <StatCard
                title="Route Continuity"
                value={continuity}
                subtitle="API-reported continuity"
                icon={Route}
              />
              <StatCard
                title="GPS Observations"
                value={diagnostics.observations ?? '—'}
                subtitle="Observations processed"
                icon={Activity}
              />
              <StatCard
                title="Candidate Segments"
                value={
                  diagnostics.candidates?.toLocaleString() ?? '—'
                }
                subtitle="Candidates evaluated"
                icon={Database}
              />
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-bold text-slate-900">
                Prediction Diagnostics
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Diagnostic information returned by the backend.
              </p>

              <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  {
                    label: 'Empty candidate observations',
                    value: diagnostics.empty_candidate_observations,
                  },
                  {
                    label: 'Fallback observations',
                    value: diagnostics.fallback_observations,
                  },
                  {
                    label: 'Disconnected transitions',
                    value: diagnostics.disconnected_transitions,
                  },
                  {
                    label: 'Predicted arc IDs',
                    value: prediction.predicted_arc_ids?.length ?? 0,
                  },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="rounded-xl bg-slate-50 p-4"
                  >
                    <p className="text-sm text-slate-500">{item.label}</p>
                    <p className="mt-2 text-2xl font-bold text-slate-900">
                      {item.value ?? '—'}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-5 rounded-xl bg-blue-50 p-4">
                <p className="text-sm font-semibold text-blue-900">
                  Accuracy method
                </p>
                <p className="mt-1 text-sm text-blue-800">
                  {prediction.accuracy_method || 'Not provided by API'}
                </p>
              </div>

              <p className="mt-4 text-xs text-slate-400">
                Accuracy is the metric reported by the API, not a prediction
                confidence score.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    Predicted Road Segments
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Consecutive repeated arc IDs are grouped together.
                  </p>
                </div>
                <span className="rounded-lg bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-700">
                  {prediction.predicted_arc_ids?.length ?? 0} predictions
                </span>
              </div>

              <div className="mt-5 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500">
                      <th className="px-3 py-3 font-semibold">Sequence</th>
                      <th className="px-3 py-3 font-semibold">Arc ID</th>
                      <th className="px-3 py-3 font-semibold">
                        Consecutive observations
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictedSegments.slice(0, 100).map((segment, index) => (
                      <tr
                        key={`${segment.arcId}-${index}`}
                        className="border-b border-slate-100"
                      >
                        <td className="px-3 py-3 text-slate-500">
                          {index + 1}
                        </td>
                        <td className="px-3 py-3 font-semibold text-slate-800">
                          {segment.arcId}
                        </td>
                        <td className="px-3 py-3 text-slate-600">
                          {segment.count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {predictedSegments.length > 100 && (
                  <p className="mt-4 text-sm text-slate-500">
                    Showing first 100 grouped segments out of{' '}
                    {predictedSegments.length}.
                  </p>
                )}

                {predictedSegments.length === 0 && (
                  <p className="py-6 text-center text-slate-500">
                    No predicted arc IDs were returned.
                  </p>
                )}
              </div>
            </div>
          </>
        )}

        {!prediction && !predictionLoading && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
              <Zap size={27} />
            </div>
            <h2 className="mt-4 text-lg font-bold text-slate-900">
              Ready to run map matching
            </h2>
            <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
              Select an available trip above and click Run Prediction to see
              the model output and evaluation diagnostics.
            </p>
          </div>
        )}
      </div>
    )
  }

  function renderModelPerformance() {
    return (
      <div className="space-y-6">
        <div>
          <p className="text-sm font-semibold text-blue-600">EVALUATION</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Model Performance
          </h1>
          <p className="mt-2 text-slate-500">
            Overview of the algorithms considered in the project.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          {modelNames.map((name, index) => (
            <div
              key={name}
              className="rounded-2xl border border-slate-200 bg-white p-6"
            >
              <div className="flex items-center justify-between">
                <div className="rounded-xl bg-blue-50 p-3 text-blue-600">
                  <BarChart3 size={22} />
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
                  {index === 0 ? 'Integrated model' : 'Comparison model'}
                </span>
              </div>
              <h2 className="mt-4 font-bold text-slate-900">{name}</h2>
              <p className="mt-2 text-sm text-slate-500">
                {index === 0
                  ? 'Used in the current map matching reconstruction pipeline.'
                  : 'Included for model comparison and evaluation.'}
              </p>
              <div className="mt-5 border-t border-slate-100 pt-4">
                <p className="text-sm text-slate-400">
                  Detailed comparative metrics are not connected to this page
                  yet.
                </p>
              </div>
            </div>
          ))}
        </div>

        {prediction && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="font-bold text-slate-900">
              Latest HMM API evaluation
            </h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-sm text-slate-500">Reported accuracy</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {(prediction.accuracy * 100).toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Route continuity</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {(prediction.route_continuity * 100).toFixed(2)}%
                </p>
              </div>
            </div>
            <p className="mt-4 text-xs text-slate-400">
              These metrics belong to the selected trip's API response; they
              are not a side-by-side comparison of all five models.
            </p>
          </div>
        )}
      </div>
    )
  }

  function renderPage() {
    switch (activePage) {
      case 'Dashboard':
        return renderDashboard()
      case 'Upload Trip':
        return renderUpload()
      case 'Map Matching':
        return renderMapMatching()
      case 'Results':
        return renderResults()
      case 'Model Performance':
        return renderModelPerformance()
      default:
        return renderDashboard()
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {menuOpen && (
        <button
          aria-label="Close navigation"
          onClick={() => setMenuOpen(false)}
          className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:translate-x-0 ${
          menuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-20 items-center justify-between border-b border-slate-100 px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-600 p-2 text-white">
              <Route size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">PathSnap</h1>
              <p className="text-xs text-slate-500">ML Hackathon</p>
            </div>
          </div>
          <button
            onClick={() => setMenuOpen(false)}
            className="text-slate-500 lg:hidden"
          >
            <X size={21} />
          </button>
        </div>

        <div className="px-4 py-6">
          <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Workspace
          </p>
          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const active = activePage === item.name

              return (
                <button
                  key={item.name}
                  onClick={() => {
                    setActivePage(item.name)
                    setMenuOpen(false)
                  }}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
                    active
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Icon size={19} />
                  {item.name}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="mt-auto border-t border-slate-100 p-5">
          <div className="rounded-xl bg-slate-50 p-4">
            <div className="flex items-center gap-2">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  apiStatus === 'Connected' ? 'bg-green-500' : 'bg-amber-500'
                }`}
              />
              <p className="text-sm font-semibold text-slate-700">
                {apiStatus}
              </p>
            </div>
            <p className="mt-2 text-xs text-slate-500">FastAPI backend</p>
          </div>
          <p className="mt-4 text-center text-xs text-slate-400">
            PathSnap ML Hackathon
          </p>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-slate-200 bg-white/90 px-5 backdrop-blur sm:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMenuOpen(true)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
            >
              <Menu size={22} />
            </button>
            <div>
              <p className="text-sm font-semibold text-slate-800">
                {activePage}
              </p>
              <p className="text-xs text-slate-400">
                PathSnap / {activePage}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2">
            <span
              className={`h-2 w-2 rounded-full ${
                apiStatus === 'Connected' ? 'bg-green-500' : 'bg-amber-500'
              }`}
            />
            <span className="text-xs font-medium text-slate-600">
              {apiStatus}
            </span>
          </div>
        </header>

        <main className="mx-auto max-w-7xl p-5 sm:p-8">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}

export default App
