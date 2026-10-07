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

const MapView = ({ markers = [], height = '600px', onMarkerClick }) => {
  const ref = useRef(null);
  const map = useRef(null);
  const layer = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    map.current = L.map(ref.current).setView(DEFAULT_CENTER, 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
    }).addTo(map.current);
    layer.current = L.layerGroup().addTo(map.current);
    return () => { map.current?.remove(); map.current = null; };
  }, []);

  useEffect(() => {
    if (!map.current || !layer.current) return;
    layer.current.clearLayers();

    // Map markers may carry location directly or via location.latitude
    const valid = markers.filter((m) => {
      const lat = m.latitude ?? m.location?.latitude;
      const lng = m.longitude ?? m.location?.longitude;
      return lat && lng;
    });

    const bounds = [];
    valid.forEach((m) => {
      const lat = m.latitude ?? m.location.latitude;
      const lng = m.longitude ?? m.location.longitude;
      const marker = L.marker([lat, lng]).addTo(layer.current);
      marker.bindPopup(
        `<div class="map-popup">
           <strong>${m.material_name}</strong><br/>
           ${Number(m.quantity).toLocaleString()} ${m.unit}<br/>
           ${m.asking_price ? `₹ ${m.asking_price}` : 'Price on request'}<br/>
           <a href="/marketplace/${m.id}">View Details</a>
         </div>`
      );
      if (onMarkerClick) marker.on('click', () => onMarkerClick(m));
      bounds.push([lat, lng]);
    });

    if (bounds.length === 1) map.current.setView(bounds[0], 10);
    else if (bounds.length > 1) map.current.fitBounds(bounds, { padding: [40, 40] });
  }, [markers, onMarkerClick]);

  return <div ref={ref} style={{ height, width: '100%', borderRadius: 12 }} />;
};

export default MapView;