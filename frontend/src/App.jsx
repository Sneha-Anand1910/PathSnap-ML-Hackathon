
import { useState } from 'react'
import {
  LayoutDashboard, Upload, Map, Route, ChartNoAxesCombined,
  Settings, Bell, Search, ArrowUpRight, ArrowRight,
  MapPin, CheckCircle2, Activity, Menu, X, Navigation,
  Zap, FileText, File, Trash2, CloudUpload, Clock
} from 'lucide-react'

import RouteMap from './components/RouteMap'

const navigation = [
  { name: 'Dashboard', icon: LayoutDashboard },
  { name: 'Upload Trip', icon: Upload },
  { name: 'Map Matching', icon: Map },
  { name: 'Results', icon: Route },
  { name: 'Model Performance', icon: ChartNoAxesCombined },
]

const stats = [
  { title: 'Total Trips', value: '80', subtitle: 'Training trips available', icon: MapPin, color: 'blue' },
  { title: 'Processed Trips', value: '80', subtitle: 'Trips validated', icon: CheckCircle2, color: 'green' },
  { title: 'Models Trained', value: '5', subtitle: 'Classification models', icon: Activity, color: 'purple' },
  { title: 'Best Model', value: 'Pending', subtitle: 'Awaiting final evaluation', icon: Zap, color: 'orange' },
]

const trips = ['00000001', '00000002', '00000003', '00000004']

function App() {
  const [activePage, setActivePage] = useState('Dashboard')
  const [menuOpen, setMenuOpen] = useState(false)
  const [files, setFiles] = useState([])
  const [tripName, setTripName] = useState('')
  const [message, setMessage] = useState('')
  const [dragging, setDragging] = useState(false)

  function addFiles(selectedFiles) {
    const allowed = ['.track', '.nodes', '.arcs', '.route', '.csv', '.zip']

    const valid = Array.from(selectedFiles).filter(file =>
      allowed.some(ext => file.name.toLowerCase().endsWith(ext))
    )

    setFiles(previous => [
      ...previous,
      ...valid.filter(file => !previous.some(old => old.name === file.name))
    ])

    setMessage(
      valid.length === 0
        ? 'Please select .track, .nodes, .arcs, .route, .csv or .zip files.'
        : `${valid.length} file(s) added successfully.`
    )
  }

  function removeFile(name) {
    setFiles(previous => previous.filter(file => file.name !== name))
  }

  function handleUpload() {
    if (!tripName.trim()) {
      setMessage('Please enter a trip name or ID.')
      return
    }

    if (files.length === 0) {
      setMessage('Please select at least one file.')
      return
    }

    setMessage('Files selected successfully! Backend integration is the next step.')
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <div className="flex min-h-screen">

        {/* SIDEBAR */}
        <aside className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:static lg:translate-x-0 ${
          menuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}>
          <div className="flex h-20 items-center justify-between border-b border-slate-100 px-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
                <Navigation size={22} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">PathSnap</h1>
                <p className="text-xs text-slate-400">Intelligent Map Matching</p>
              </div>
            </div>
            <button onClick={() => setMenuOpen(false)} className="lg:hidden">
              <X size={20} />
            </button>
          </div>

          <div className="px-4 py-7">
            <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
              Workspace
            </p>

            <nav className="space-y-1">
              {navigation.map(item => {
                const Icon = item.icon
                const active = activePage === item.name

                return (
                  <button
                    key={item.name}
                    onClick={() => {
                      setActivePage(item.name)
                      setMenuOpen(false)
                      setMessage('')
                    }}
                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
                      active
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    <Icon size={19} />
                    {item.name}
                    {active && <div className="ml-auto h-2 w-2 rounded-full bg-blue-600" />}
                  </button>
                )
              })}
            </nav>
          </div>

          <div className="mt-auto p-4">
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
                <Activity size={17} className="text-blue-600" />
                Project status
              </div>

              <div className="mb-2 flex items-center justify-between text-xs">
                <span className="text-slate-500">Development</span>
                <span className="font-semibold text-blue-600">In progress</span>
              </div>

              <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full w-2/3 rounded-full bg-blue-600" />
              </div>

              <p className="mt-3 text-xs text-slate-400">
                PathSnap ML Hackathon Project
              </p>
            </div>

            <button className="mt-4 flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-slate-500 hover:bg-slate-50">
              <Settings size={19} />
              Settings
            </button>
          </div>
        </aside>

        {/* MOBILE OVERLAY */}
        {menuOpen && (
          <div
            className="fixed inset-0 z-20 bg-slate-900/30 lg:hidden"
            onClick={() => setMenuOpen(false)}
          />
        )}

        {/* MAIN CONTENT */}
        <main className="min-w-0 flex-1">

          {/* TOPBAR */}
          <header className="sticky top-0 z-10 flex h-20 items-center justify-between border-b border-slate-200 bg-white/95 px-5 backdrop-blur md:px-8">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setMenuOpen(true)}
                className="rounded-lg p-2 hover:bg-slate-100 lg:hidden"
              >
                <Menu size={21} />
              </button>

              <div>
                <p className="text-sm text-slate-400">Workspace / {activePage}</p>
                <h2 className="text-lg font-bold text-slate-900">{activePage}</h2>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 md:flex">
                <Search size={16} className="text-slate-400" />
                <span className="text-sm text-slate-400">Search...</span>
              </div>

              <button className="relative rounded-xl border border-slate-200 p-2.5 text-slate-500">
                <Bell size={18} />
              </button>

              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">
                PS
              </div>
            </div>
          </header>

          <div className="mx-auto max-w-7xl space-y-7 p-5 md:p-8">

            {/* DASHBOARD */}
            {activePage === 'Dashboard' && (
              <>
                <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                  <div>
                    <p className="text-sm font-medium text-blue-600">PATHSNAP ANALYTICS</p>
                    <h1 className="mt-2 text-3xl font-bold text-slate-900">
                      Welcome to PathSnap
                    </h1>
                    <p className="mt-2 text-sm text-slate-500">
                      Monitor GPS data, map matching and machine learning performance.
                    </p>
                  </div>

                  <button
                    onClick={() => setActivePage('Upload Trip')}
                    className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700"
                  >
                    <Upload size={17} />
                    Upload a trip
                  </button>
                </section>

                <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  {stats.map(stat => {
                    const Icon = stat.icon
                    const colors = {
                      blue: 'bg-blue-50 text-blue-600',
                      green: 'bg-emerald-50 text-emerald-600',
                      purple: 'bg-violet-50 text-violet-600',
                      orange: 'bg-orange-50 text-orange-600'
                    }

                    return (
                      <div key={stat.title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-slate-500">{stat.title}</p>
                          <div className={`rounded-xl p-2.5 ${colors[stat.color]}`}>
                            <Icon size={20} />
                          </div>
                        </div>
                        <h3 className="mt-5 text-3xl font-bold text-slate-900">{stat.value}</h3>
                        <p className="mt-1 text-xs text-slate-400">{stat.subtitle}</p>
                      </div>
                    )
                  })}
                </section>

                <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
                  <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm xl:col-span-2">
                    <div className="flex items-center justify-between border-b border-slate-100 p-5">
                      <div>
                        <h3 className="font-bold text-slate-900">Route visualization</h3>
                        <p className="mt-1 text-xs text-slate-400">Illustrative GPS route preview</p>
                      </div>
                      <button
                        onClick={() => setActivePage('Map Matching')}
                        className="flex items-center gap-1 text-sm font-semibold text-blue-600"
                      >
                        Explore map <ArrowUpRight size={16} />
                      </button>
                    </div>

                    <div className="relative h-72 overflow-hidden bg-slate-100">
                      <div
                        className="absolute inset-0 opacity-60"
                        style={{
                          backgroundImage: 'linear-gradient(#dbe4ed 1px, transparent 1px), linear-gradient(90deg, #dbe4ed 1px, transparent 1px)',
                          backgroundSize: '38px 38px'
                        }}
                      />
                      <svg viewBox="0 0 700 300" className="absolute inset-0 h-full w-full" preserveAspectRatio="none">
                        <path d="M-20 70 L130 100 L230 65 L360 110 L490 75 L720 120 M30 280 L150 210 L250 240 L390 175 L530 200 L710 145 M180 -20 L220 70 L260 140 L240 220 L280 330 M510 -20 L470 75 L500 140 L450 230 L480 330" stroke="#CBD5E1" strokeWidth="12" fill="none" />
                        <path d="M30 280 L150 210 L250 240 L390 175 L530 200 L710 145" stroke="#2563EB" strokeWidth="5" fill="none" />
                        <circle cx="30" cy="280" r="8" fill="#16A34A" stroke="white" strokeWidth="3" />
                        <circle cx="710" cy="145" r="8" fill="#DC2626" stroke="white" strokeWidth="3" />
                      </svg>
                      <div className="absolute bottom-4 left-4 rounded-xl bg-white/95 px-4 py-3 shadow-sm">
                        <p className="text-xs font-medium text-slate-600">Illustrative matched route</p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <h3 className="font-bold text-slate-900">Project overview</h3>
                    <p className="mt-1 text-xs text-slate-400">Current development progress</p>

                    <div className="mt-7 space-y-6">
                      {[
                        { name: 'Data preprocessing', detail: 'Completed', width: '100%', color: 'bg-emerald-500' },
                        { name: 'Feature engineering', detail: 'In progress', width: '75%', color: 'bg-blue-500' },
                        { name: 'Model training', detail: 'In progress', width: '65%', color: 'bg-violet-500' },
                        { name: 'Final evaluation', detail: 'Pending', width: '25%', color: 'bg-orange-400' }
                      ].map(item => (
                        <div key={item.name}>
                          <div className="mb-2 flex justify-between gap-2 text-sm">
                            <span className="font-medium text-slate-700">{item.name}</span>
                            <span className="text-xs text-slate-400">{item.detail}</span>
                          </div>
                          <div className="h-2 rounded-full bg-slate-100">
                            <div className={`h-2 rounded-full ${item.color}`} style={{ width: item.width }} />
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="mt-8 rounded-xl bg-blue-50 p-4">
                      <p className="text-sm font-semibold text-blue-800">ML pipeline</p>
                      <p className="mt-2 text-xs leading-5 text-blue-700">
                        Final model results will appear here once available.
                      </p>
                    </div>
                  </div>
                </section>

                <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                  <div className="flex items-center justify-between border-b border-slate-100 p-5">
                    <div>
                      <h3 className="font-bold text-slate-900">Recent trips</h3>
                      <p className="mt-1 text-xs text-slate-400">Sample training dataset records</p>
                    </div>
                    <button onClick={() => setActivePage('Results')} className="flex items-center gap-1 text-sm font-semibold text-blue-600">
                      View all <ArrowRight size={16} />
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[500px] text-left">
                      <thead className="bg-slate-50 text-xs uppercase text-slate-400">
                        <tr>
                          <th className="px-5 py-4">Trip ID</th>
                          <th className="px-5 py-4">Dataset</th>
                          <th className="px-5 py-4">Data type</th>
                          <th className="px-5 py-4">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {trips.map(id => (
                          <tr key={id}>
                            <td className="px-5 py-4 text-sm font-semibold">{id}</td>
                            <td className="px-5 py-4 text-sm text-slate-500">Training dataset</td>
                            <td className="px-5 py-4 text-sm text-slate-500">GPS observations</td>
                            <td className="px-5 py-4">
                              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                                Validated
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </>
            )}

            {/* UPLOAD TRIP */}
            {activePage === 'Upload Trip' && (
              <section className="mx-auto max-w-4xl space-y-6">
                <div>
                  <p className="text-sm font-semibold text-blue-600">DATA INPUT</p>
                  <h1 className="mt-2 text-3xl font-bold text-slate-900">Upload a Trip</h1>
                  <p className="mt-2 text-sm text-slate-500">
                    Upload GPS trajectory and road network files to prepare a trip for map matching.
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:p-8">
                  <label className="mb-2 block text-sm font-semibold text-slate-700">
                    Trip name or ID
                  </label>

                  <input
                    value={tripName}
                    onChange={e => setTripName(e.target.value)}
                    placeholder="e.g. 00000034 or My GPS Trip"
                    className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  />

                  <div className="mb-3 mt-8 flex items-center justify-between">
                    <label className="text-sm font-semibold text-slate-700">Upload your dataset files</label>
                    <span className="text-xs text-slate-400">Multiple files supported</span>
                  </div>

                  <label
                    onDragOver={e => { e.preventDefault(); setDragging(true) }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={e => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files) }}
                    className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-5 py-12 text-center ${
                      dragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-blue-50/50'
                    }`}
                  >
                    <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-blue-600">
                      <CloudUpload size={28} />
                    </div>
                    <p className="font-semibold text-slate-800">
                      Drop your files here or <span className="text-blue-600">browse</span>
                    </p>
                    <p className="mt-2 text-xs text-slate-400">
                      Supported formats: .track, .nodes, .arcs, .route, .csv, .zip
                    </p>
                    <input
                      type="file"
                      multiple
                      accept=".track,.nodes,.arcs,.route,.csv,.zip"
                      className="hidden"
                      onChange={e => {
                        addFiles(e.target.files)
                        e.target.value = ''
                      }}
                    />
                  </label>

                  <div className="mt-7 rounded-xl bg-blue-50 p-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-blue-800">
                      <FileText size={18} /> Required dataset files
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                      {[
                        ['.track', 'GPS coordinates'],
                        ['.nodes', 'Road nodes'],
                        ['.arcs', 'Road connections'],
                        ['.route', 'Reference route']
                      ].map(([ext, label]) => (
                        <div key={ext} className="rounded-lg bg-white p-3">
                          <p className="text-sm font-bold text-blue-700">{ext}</p>
                          <p className="mt-1 text-xs text-slate-500">{label}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {files.length > 0 && (
                    <div className="mt-7">
                      <div className="mb-3 flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-slate-700">
                          Selected files ({files.length})
                        </h3>
                        <button onClick={() => setFiles([])} className="text-xs text-red-500">
                          Remove all
                        </button>
                      </div>

                      <div className="space-y-2">
                        {files.map(file => (
                          <div key={file.name} className="flex items-center justify-between rounded-xl border border-slate-200 p-3">
                            <div className="flex min-w-0 items-center gap-3">
                              <div className="rounded-lg bg-slate-100 p-2 text-slate-500">
                                <File size={18} />
                              </div>
                              <div className="min-w-0">
                                <p className="truncate text-sm font-medium text-slate-700">{file.name}</p>
                                <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                              </div>
                            </div>
                            <button onClick={() => removeFile(file.name)} className="ml-3 rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-500">
                              <Trash2 size={17} />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {message && (
                    <p role="status" className="mt-5 rounded-xl bg-blue-50 p-3 text-sm text-blue-700">
                      {message}
                    </p>
                  )}

                  <div className="mt-7 flex flex-col justify-between gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:items-center">
                    <p className="text-xs text-slate-400">Files are selected locally. No server upload yet.</p>
                    <button onClick={handleUpload} className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700">
                      <Upload size={17} />Continue
                    </button>
                  </div>
                </div>
              </section>
            )}

            {/* MAP MATCHING */}
            {activePage === 'Map Matching' && (
              <section className="space-y-6">
                <div>
                  <p className="text-sm font-semibold text-blue-600">ROUTE ANALYSIS</p>
                  <h1 className="mt-2 text-3xl font-bold text-slate-900">
                    Interactive Map
                  </h1>
                  <p className="mt-2 text-sm text-slate-500">
                    Explore GPS observations and the illustrative matched route.
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="mb-5 flex flex-wrap items-center gap-5 text-sm">
                    <span className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full bg-orange-500" />
                      Original GPS points
                    </span>
                    <span className="flex items-center gap-2">
                      <span className="h-1 w-5 rounded bg-blue-600" />
                      Matched route (demo)
                    </span>
                  </div>

                  <RouteMap />

                  <p className="mt-4 text-xs text-slate-400">
                    Demo coordinates near Bengaluru. Actual trip predictions will be connected later.
                  </p>
                </div>
              </section>
            )}

            {/* RESULTS PAGE */}
            {activePage === 'Results' && (
              <section className="space-y-6">

                <div>
                  <p className="text-sm font-semibold text-blue-600">TRIP ANALYSIS</p>
                  <h1 className="mt-2 text-3xl font-bold text-slate-900">
                    Map Matching Results
                  </h1>
                  <p className="mt-2 text-sm text-slate-500">
                    View GPS observations, predicted routes and model outputs.
                  </p>
                </div>

                {/* Trip information cards */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">

                  <div className="rounded-2xl border border-slate-200 bg-white p-5">
                    <p className="text-sm text-slate-500">Trip ID</p>
                    <h2 className="mt-3 text-2xl font-bold text-slate-900">
                      00000034
                    </h2>
                    <p className="mt-1 text-xs text-slate-400">Demo trip</p>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white p-5">
                    <p className="text-sm text-slate-500">Processing status</p>
                    <h2 className="mt-3 text-2xl font-bold text-amber-600">
                      Awaiting ML
                    </h2>
                    <p className="mt-1 text-xs text-slate-400">Backend not connected</p>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white p-5">
                    <p className="text-sm text-slate-500">Prediction confidence</p>
                    <h2 className="mt-3 text-2xl font-bold text-slate-900">
                      —
                    </h2>
                    <p className="mt-1 text-xs text-slate-400">Not yet calculated</p>
                  </div>

                </div>

                {/* Route comparison */}
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

                  <div className="mb-5">
                    <h2 className="text-lg font-bold text-slate-900">
                      Route comparison
                    </h2>
                    <p className="mt-1 text-sm text-slate-500">
                      Visualize the GPS trajectory and matched road route.
                    </p>
                  </div>

                  <div className="mb-5 flex flex-wrap gap-5 text-sm">
                    <span className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full bg-orange-500" />
                      Original GPS points
                    </span>

                    <span className="flex items-center gap-2">
                      <span className="h-1 w-5 rounded bg-blue-600" />
                      Demo matched route
                    </span>
                  </div>

                  <RouteMap />

                  <p className="mt-4 text-xs text-slate-400">
                    Illustrative route only. Actual model predictions will appear after backend integration.
                  </p>

                </div>

                {/* Predicted segments */}
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

                  <h2 className="text-lg font-bold text-slate-900">
                    Predicted road segments
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Road segment predictions generated by the ML model.
                  </p>

                  <div className="mt-6 overflow-x-auto">
                    <table className="w-full min-w-[500px] text-left">

                      <thead className="bg-slate-50 text-xs uppercase text-slate-400">
                        <tr>
                          <th className="px-4 py-3">Segment</th>
                          <th className="px-4 py-3">Predicted road</th>
                          <th className="px-4 py-3">Confidence</th>
                          <th className="px-4 py-3">Status</th>
                        </tr>
                      </thead>

                      <tbody>
                        <tr>
                          <td colSpan="4" className="px-4 py-10 text-center">
                            <Activity className="mx-auto mb-3 text-slate-300" size={28} />
                            <p className="font-medium text-slate-600">
                              No predictions available yet
                            </p>
                            <p className="mt-1 text-xs text-slate-400">
                              Connect the trained ML model to display predicted road segments.
                            </p>
                          </td>
                        </tr>
                      </tbody>

                    </table>
                  </div>

                </div>

                {/* Evaluation information */}
                <div className="rounded-2xl border border-blue-100 bg-blue-50 p-5">
                  <div className="flex items-center gap-2 font-semibold text-blue-800">
                    <Activity size={19} />
                    Model evaluation
                  </div>

                  <p className="mt-2 text-sm leading-6 text-blue-700">
                    Model accuracy, route matching performance and prediction metrics will be displayed here once the trained models are connected.
                  </p>
                </div>

              </section>
            )}

            {/* MODEL PERFORMANCE */}
            {activePage === 'Model Performance' && (
              <section className="space-y-6">

                <div>
                  <p className="text-sm font-semibold text-blue-600">ML EVALUATION</p>
                  <h1 className="mt-2 text-3xl font-bold text-slate-900">
                    Model Performance
                  </h1>
                  <p className="mt-2 text-sm text-slate-500">
                    Compare the five machine learning models used in PathSnap.
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {[
                    'Logistic Regression',
                    'K-Nearest Neighbors',
                    'Decision Tree',
                    'Random Forest',
                    'Gradient Boosting'
                  ].map(model => (
                    <div key={model} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                      <div className="flex items-center gap-3">
                        <div className="rounded-xl bg-blue-50 p-3 text-blue-600">
                          <ChartNoAxesCombined size={21} />
                        </div>
                        <h3 className="font-semibold text-slate-800">{model}</h3>
                      </div>
                      <p className="mt-5 text-sm text-slate-400">
                        Evaluation metrics pending integration.
                      </p>
                    </div>
                  ))}
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900">
                    Model comparison
                  </h2>
                  <p className="mt-2 text-sm text-slate-500">
                    Accuracy, precision, recall, F1-score and cross-validation results will be visualized here using actual evaluation outputs.
                  </p>
                  <div className="mt-6 rounded-xl bg-slate-50 p-10 text-center">
                    <ChartNoAxesCombined className="mx-auto mb-3 text-slate-300" size={36} />
                    <p className="font-medium text-slate-600">
                      Waiting for evaluation data
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      No performance numbers have been populated yet.
                    </p>
                  </div>
                </div>

              </section>
            )}

            {/* FOOTER */}
            <footer className="flex flex-col justify-between gap-2 border-t border-slate-200 py-5 text-xs text-slate-400 sm:flex-row">
              <p>© 2026 PathSnap ML Hackathon Project</p>
              <p className="flex items-center gap-1">
                Built for intelligent GPS map matching <Clock size={13} />
              </p>
            </footer>

          </div>
        </main>
      </div>
    </div>
  )
}

export default App
