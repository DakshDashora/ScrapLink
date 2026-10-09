import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const DEFAULT_CENTER = [22.9734, 78.6569];

const LocationPicker = ({ latitude, longitude, onChange, height = '320px' }) => {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const hasCoords = latitude && longitude;
    const center = hasCoords
      ? [Number(latitude), Number(longitude)]
      : DEFAULT_CENTER;

    mapRef.current = L.map(containerRef.current).setView(center, hasCoords ? 13 : 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
    }).addTo(mapRef.current);

    mapRef.current.on('click', (e) => {
      const { lat, lng } = e.latlng;
      placeMarker(lat, lng);
      onChange?.(lat.toFixed(6), lng.toFixed(6));
    });

    if (hasCoords) placeMarker(Number(latitude), Number(longitude));

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    if (latitude && longitude) {
      const lat = Number(latitude);
      const lng = Number(longitude);
      placeMarker(lat, lng);
      mapRef.current.setView([lat, lng], 13);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latitude, longitude]);

  const placeMarker = (lat, lng) => {
    if (!mapRef.current) return;
    if (markerRef.current) {
      markerRef.current.setLatLng([lat, lng]);
    } else {
      markerRef.current = L.marker([lat, lng], { draggable: true })
        .addTo(mapRef.current)
        .on('dragend', (e) => {
          const p = e.target.getLatLng();
          onChange?.(p.lat.toFixed(6), p.lng.toFixed(6));
        });
    }
  };

  return (
    <>
      <div
        ref={containerRef}
        style={{ height, width: '100%', borderRadius: 10, border: '1px solid #e2e8f0' }}
      />
      <p className="map-hint">
        Click anywhere on the map to move the pin, or drag it to fine-tune.
      </p>
    </>
  );
};

export default LocationPicker;