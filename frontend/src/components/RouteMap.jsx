
import { MapContainer, TileLayer, Marker, Polyline, Popup, CircleMarker } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

// Illustrative GPS coordinates for testing.
// These will later be replaced with actual trip data.
const gpsPoints = [
  [12.9716, 77.5946],
  [12.9722, 77.5960],
  [12.9730, 77.5972],
  [12.9740, 77.5980],
  [12.9750, 77.5995],
]

const matchedRoute = [
  [12.9715, 77.5945],
  [12.9724, 77.5958],
  [12.9732, 77.5970],
  [12.9742, 77.5982],
  [12.9752, 77.5994],
]

export default function RouteMap() {
  return (
    <div className="h-[450px] w-full overflow-hidden rounded-2xl border border-slate-200">
      <MapContainer
        center={[12.9733, 77.5970]}
        zoom={16}
        scrollWheelZoom={true}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Predicted matched road route */}
        <Polyline
          positions={matchedRoute}
          pathOptions={{ color: '#2563eb', weight: 6 }}
        />

        {/* Original GPS observations */}
        {gpsPoints.map((point, index) => (
          <CircleMarker
            key={index}
            center={point}
            radius={6}
            pathOptions={{
              color: '#ffffff',
              weight: 2,
              fillColor: '#f97316',
              fillOpacity: 1,
            }}
          >
            <Popup>GPS observation {index + 1}</Popup>
          </CircleMarker>
        ))}

        <Marker position={matchedRoute[0]}>
          <Popup>Trip start</Popup>
        </Marker>

        <Marker position={matchedRoute[matchedRoute.length - 1]}>
          <Popup>Trip destination</Popup>
        </Marker>
      </MapContainer>
    </div>
  )
}
