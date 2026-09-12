import { useDispatch, useSelector } from 'react-redux';
import { predictPrice, clearPrediction } from '../../features/listings/listingSlice';

const PriceRecommendation = ({ listing }) => {
  const dispatch = useDispatch();
  const { prediction, isLoading } = useSelector((s) => s.listings);

  const handlePredict = () => {
    dispatch(
      predictPrice({
        category_id: listing.category_id,
        material_name: listing.material_name,
        grade: listing.grade,
        quantity: Number(listing.quantity),
        unit: listing.unit,
        location: listing.location,
      })
    );
  };

  return (
    <div className="price-recommendation">
      <button className="btn-primary" onClick={handlePredict} disabled={isLoading}>
        {isLoading ? 'Calculating…' : 'Get Price Recommendation'}
      </button>

      {prediction && (
        <div className="prediction-box">
          <h4>Estimated Recommended Price</h4>
          <p className="recommended-value">
            ₹ {Number(prediction.recommended_price).toLocaleString()}
            {prediction.unit ? ` / ${prediction.unit}` : ''}
          </p>
          {prediction.price_band && (
            <p className="price-band">
              Range: ₹ {prediction.price_band[0]} – ₹ {prediction.price_band[1]}
            </p>
          )}
          <p className="disclaimer">
            ⚠ This is an AI-assisted estimate based on market reference data,
            not a guaranteed transaction price.
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