// Forward geocode: address → { latitude, longitude }
export const geocodeAddress = async ({ address, city, state }) => {
  const parts = [address, city, state, 'India'].filter(Boolean);
  if (parts.length === 0) throw new Error('Please enter at least a city or state.');

  const query = encodeURIComponent(parts.join(', '));
  const url = `https://nominatim.openstreetmap.org/search?q=${query}&format=json&limit=1`;

  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error('Geocoding request failed');

  const data = await res.json();
  if (!data || data.length === 0) {
    throw new Error('Location not found. Try a more specific address or city.');
  }
  return {
    latitude: Number(data[0].lat).toFixed(6),
    longitude: Number(data[0].lon).toFixed(6),
    displayName: data[0].display_name,
  };
};

// Reverse geocode: coordinates → { city, state, address }
export const reverseGeocode = async (latitude, longitude) => {
  const url =
    `https://nominatim.openstreetmap.org/reverse?` +
    `lat=${latitude}&lon=${longitude}&format=json&addressdetails=1`;

  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error('Reverse geocoding failed');

  const data = await res.json();
  const a = data.address || {};

  const city =
    a.city || a.town || a.village || a.suburb || a.county || '';
  const state = a.state || a.state_district || '';
  const address =
    [a.road, a.neighbourhood, a.suburb].filter(Boolean).join(', ') ||
    data.display_name?.split(',').slice(0, 2).join(', ') ||
    '';

  return { city, state, address };
};