# Scoring Weights Calibration

## Current Weights (v1.0-mvp)
- Science: 0.30
- Patent: 0.20
- Trend: 0.20
- Trade: 0.30

## Calibration Cases

| Case | Science | Patent | Trend | Trade | Expected Recommendation |
|---|---|---|---|---|---|
| Cocoa flavanol (all domains) | 80 | 60 | 50 | 70 | Investigate |
| Quinoa protein (partial) | 40 | 20 | 0 | 30 | Deprioritize / Insufficient evidence |
| Novel ingredient (science only) | 90 | 0 | 0 | 0 | Insufficient evidence |

## Coverage Thresholds
- `< 60%` coverage → `Insufficient evidence`
- `>= 60%` and score `< 50` → `Deprioritize`
- `>= 50` and score `< 70` → `Validate`
- `>= 70` → `Investigate`

## Next Steps
- [ ] Run calibration cases through system
- [ ] Adjust weights based on analyst feedback
- [ ] Document final weights in `scoring.py`
