import { useState } from 'react';

export const useGeolocation = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const requestPosition = () =>
    new Promise((resolve, reject) => {
      if (!('geolocation' in navigator)) {
        const msg = 'Geolocation is not supported by this browser.';
        setError(msg);
        reject(new Error(msg));
        return;
      }

      setLoading(true);
      setError(null);

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLoading(false);
          resolve({
            latitude: pos.coords.latitude.toFixed(6),
            longitude: pos.coords.longitude.toFixed(6),
            accuracy: pos.coords.accuracy,
          });
        },
        (err) => {
          setLoading(false);
          let msg = 'Could not get your location.';
          if (err.code === 1) msg = 'Permission denied. Allow location access in your browser.';
          else if (err.code === 2) msg = 'Location unavailable. Try again in a moment.';
          else if (err.code === 3) msg = 'Location request timed out.';
          setError(msg);
          reject(new Error(msg));
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    });

  return { requestPosition, loading, error };
};