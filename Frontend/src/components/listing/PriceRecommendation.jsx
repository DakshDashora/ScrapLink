import { useDispatch, useSelector } from 'react-redux';
import { predictPrice, clearPrediction } from '../../redux/slices/listingSlice';

const PriceRecommendation = ({ listing }) => {
  const dispatch = useDispatch();
  const { prediction, isLoading, error } = useSelector((s) => s.listings);

  const handlePredict = () => {
    // ✅ Send EXACTLY what the backend expects
    dispatch(predictPrice({
      commodity: listing.material_name,      // e.g., "Copper"
      scrap_type: listing.grade || "", // e.g., "99.9%"
    }));
  };

  return (
    <div className="price-recommendation">
      <button className="btn-primary" onClick={handlePredict} disabled={isLoading}>
        {isLoading ? 'Calculating…' : 'Get Price Recommendation'}
      </button>

      {error && <div className="error-message">{error}</div>}

      {prediction && (
        <div className="prediction-box">
          <h4>Estimated Recommended Price</h4>
          <p className="recommended-value">
            ₹ {Number(prediction.recommended_price ?? prediction.price).toLocaleString()}
            {prediction.unit ? ` / ${prediction.unit}` : ''}
          </p>
          
          {/* ✅ Fixed the price band rendering (it's an object, not an array) */}
          {prediction.price_band && (
            <p className="price-band">
              Range: ₹ {prediction.price_band.lower} – ₹ {prediction.price_band.upper}
            </p>
          )}

          <p className="disclaimer">
            ⚠ AI-assisted estimate based on market reference data — not a
            guaranteed transaction price.
          </p>
          <button className="link-button" onClick={() => dispatch(clearPrediction())}>
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};

export default PriceRecommendation;