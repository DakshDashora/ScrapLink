import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default marker icons (Vite/Webpack often break them)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const DEFAULT_CENTER = [22.9734, 78.6569]; // India

const MapView = ({ markers = [], height = '600px', onMarkerClick }) => {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    mapRef.current = L.map(containerRef.current).setView(DEFAULT_CENTER, 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
    }).addTo(mapRef.current);

    layerRef.current = L.layerGroup().addTo(mapRef.current);

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;

    layerRef.current.clearLayers();

    const validMarkers = markers.filter(
      (m) => m.location?.latitude && m.location?.longitude
    );

    const bounds = [];
    validMarkers.forEach((m) => {
      const { latitude, longitude } = m.location;
      const marker = L.marker([latitude, longitude]).addTo(layerRef.current);
      marker.bindPopup(
        `<div class="map-popup">
           <strong>${m.material_name}</strong><br/>
           ${m.quantity} ${m.unit}<br/>
           ${m.asking_price ? `₹ ${m.asking_price}` : 'Price on request'}<br/>
           <a href="/marketplace/${m.listing_id}">View Details</a>
         </div>`
      );
      if (onMarkerClick) marker.on('click', () => onMarkerClick(m));
      bounds.push([latitude, longitude]);
    });

    if (bounds.length === 1) {
      mapRef.current.setView(bounds[0], 10);
    } else if (bounds.length > 1) {
      mapRef.current.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [markers, onMarkerClick]);

  return <div ref={containerRef} style={{ height, width: '100%', borderRadius: 12 }} />;
};

export default MapView;