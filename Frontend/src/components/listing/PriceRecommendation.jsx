import { useDispatch, useSelector } from 'react-redux';
import { predictPrice, clearPrediction } from '../../redux/slices/listingSlice';

const PriceRecommendation = ({ listing }) => {
  const dispatch = useDispatch();
  const { pricePrediction, isPredicting, predictError } = useSelector(
    (s) => s.listings
  );

  const handlePredict = () => {
    const commodity = listing.material_name?.trim();
    if (!commodity) return;

    const payload = {
      commodity,
    };
    if (listing.grade?.trim()) payload.scrap_type = listing.grade.trim();
    dispatch(predictPrice(payload));
  };

  return (
    <div className="price-recommendation">
      <button
        className="btn-primary"
        onClick={handlePredict}
        disabled={isPredicting || !listing.material_name?.trim()}
      >
        {isPredicting ? 'Calculating…' : 'Get Price Recommendation'}
      </button>

      {predictError && <div className="error-message">{predictError}</div>}

      {pricePrediction && (
        <div className="prediction-box">
          <h4>Estimated Recommended Price</h4>
          <p className="recommended-value">
            ₹ {Number(pricePrediction.recommended_price).toLocaleString()}
            {pricePrediction.unit ? ` / ${pricePrediction.unit}` : ''}
          </p>
          
          {pricePrediction.price_band && (
            <p className="price-band">
              Range: ₹ {pricePrediction.price_band.lower} – ₹ {pricePrediction.price_band.upper}
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