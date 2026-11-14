import { useDispatch, useSelector } from 'react-redux';
import { predictPrice } from '../../redux/slices/listingSlice';

const PricePredictor = ({ form, onApplyPrice }) => {
  const dispatch = useDispatch();
  const { pricePrediction, isPredicting, predictError } = useSelector(
    (s) => s.listings
  );

  const handlePredict = () => {
    // Map the listing form data to the ML API payload
    const payload = {
      commodity: form.material_name || 'Steel',
      scrap_type: form.grade || 'General',
      // Time-series features are set to 0 since we don't have historical market data in this form
      lag_1: 0,
      lag_7: 0,
      lag_14: 0,
      lag_30: 0,
      rolling_mean_7: 0,
      rolling_mean_30: 0,
      rolling_std_7: 0,
      rolling_std_30: 0,
      pct_change_7: 0,
      pct_change_30: 0,
    };
    
    dispatch(predictPrice(payload));
  };

  return (
    <div className="price-predictor">
      <button
        type="button"
        className="btn-secondary suggest-price-btn"
        onClick={handlePredict}
        disabled={isPredicting || !form.material_name}
        title={!form.material_name ? "Enter a material name first" : ""}
      >
        {isPredicting ? 'Analyzing Market…' : '✨ Suggest Price'}
      </button>

      {predictError && <div className="predict-error">{predictError}</div>}

      {pricePrediction && (
        <div className="prediction-result-box">
          <div className="prediction-header">
            <strong>AI Market Estimate</strong>
            <span className="trend-badge">
              {pricePrediction.trend === 'up' ? '📈 Trending Up' : 
               pricePrediction.trend === 'down' ? '📉 Trending Down' : '➖ Stable'}
            </span>
          </div>
          
          <div className="prediction-price">
            ₹ {Number(pricePrediction.recommended_price).toLocaleString()} 
            <span className="unit"> / {pricePrediction.unit || 'kg'}</span>
          </div>
          
          <div className="prediction-band">
            Expected Range: ₹{pricePrediction.estimated_price_p10_inr_per_kg} - ₹{pricePrediction.estimated_price_p90_inr_per_kg}
          </div>

          <div className="prediction-actions">
            <button 
              type="button" 
              className="btn-primary apply-btn"
              onClick={() => onApplyPrice(pricePrediction.recommended_price)}
            >
              Use This Price
            </button>
          </div>

          <div className="prediction-disclaimer">
            {pricePrediction.disclaimer || "AI estimate based on market data. Not a guaranteed transaction price."}
          </div>
        </div>
      )}
    </div>
  );
};

export default PricePredictor;