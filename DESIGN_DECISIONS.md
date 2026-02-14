# DESIGN_DECISIONS.md

## 1️ What anomalies did you plant and why? Why are they realistic? What would each cost if undetected?

I planted anomalies that reflect real export compliance, customs, and financial control failures — not artificial ML noise.

### A. FOB Calculation Mismatch
**Anomaly:**  
`total_fob ≠ quantity × unit_price`

**Why realistic:**  
Common in ERP systems due to manual invoice entry, rounding issues, or currency conversion mistakes.

**Impact if undetected:**  
- Customs reassessment  
- GST mismatch  
- 1–5% penalty on shipment value  

**Example:**  
For a ₹25 lakh shipment: Penalty + delay cost ≈ ₹1–1.5 lakhs.

---

### B. Drawback Claimed on Rejected Shipment
**Anomaly:**  
`drawback_amount > 0` while `customs_status = rejected`

**Why realistic:**  
ERP lag or manual override errors can cause improper drawback claims.

**Impact if undetected:**  
- Full drawback recovery  
- 12–18% interest  
- Possible investigation  

**Example:**  
For ₹3 lakh drawback: Recovery + penalty ≈ ₹3.5–4 lakhs.

---

### C. Payment Status Inconsistency
**Anomaly:**  
`payment_status = received` but `days_to_payment = null`

**Why realistic:**  
Reconciliation gaps between accounting and shipping systems are common.

**Impact if undetected:**  
- False cash flow reporting  
- Credit risk blind spots  
- If buyer defaults: loss of full shipment value (₹10–30 lakhs).

---

### D. CIF Freight = 0
**Anomaly:**  
`incoterm = CIF` but `freight_cost = 0`

**Why realistic:**  
Freight must be included under CIF. Missing freight causes undervaluation.

**Impact if undetected:**  
- Customs reassessment  
- Additional duty  
- Fines  

**Example:**  
For ₹20 lakh shipment: ~₹1.5 lakh duty reassessment.

---

### E. Insurance Value Anomaly
**Anomaly:**  
Insurance not aligned with FOB (should be ~110% of FOB).

**Why realistic:**  
Common compliance oversight.

**Impact:**  
- Underinsured cargo loss  
- Audit trigger  
- Potential loss = full cargo value

---

### F. HS Code vs Product Description Mismatch
**Anomaly:**  
Semantic mismatch between HS code and product description.

**Why realistic:**  
Misclassification is one of the most common customs audit triggers.

**Impact if undetected:**  
- Differential duty demand  
- 100% penalty possible  
- Incentive clawback  

**Estimated exposure:** ₹5–10 lakhs per shipment.

---

### G. Buyer Payment Pattern Deterioration
**Anomaly:**  
Increasing payment delays over recent shipments.

**Why realistic:**  
Early sign of liquidity stress.

**Impact:**  
Full non-payment risk.

> These anomalies are realistic because they reflect known customs audit triggers and financial control failures — not synthetic statistical noise.

---

## 2️⃣ What statistical method did you use in Layer 2 and why?
**Method Used:** Z-Score (Filtered Application)

For numeric anomaly detection (e.g., payment delay, freight ratio, insurance ratio), I used:
            Z = (value − mean) / standard deviation

**Why Z-Score?**  
- Interpretable  
- Lightweight  
- Works well for normally distributed trade metrics  
- Computationally efficient  
- No training data required

**What I Considered:**

| Method            | Why Not Used                                        |
|------------------|----------------------------------------------------|
| Isolation Forest  | Overkill for 250 rows                              |
| DBSCAN            | Hard to tune, density sensitive                    |
| IQR               | Good for small samples but less stable across features |
| LOF               | More complex, harder to explain to business users |

**Why I chose Z-score:**  
- Provides explainable numeric thresholds  
- Easy to audit  
- Suitable for structured financial metrics  

**Important:**  
I did **NOT** run Z-score on the entire dataset blindly.  
I first filtered candidates using business logic to avoid unnecessary noise.

---

## 3️⃣ What exactly did you send to the LLM? How many calls? Token usage? Why Layer 2 vs Layer 3 boundary?

**What I Sent to the LLM:**  
- Rows where HS code differed from product catalog baseline  
- Buyer shipment history only when statistical layer flagged payment anomalies  
- Final anomaly summary (not raw dataset)

**What I Did NOT Send:**  
- Entire 250 rows  
- Full shipment dataset  
- Redundant structured calculations

**Number of Calls:**  
- HS validations: 2 calls  
- Executive summary: 1 call  
- Buyer pattern analysis: 0–1 calls  
- **Total:** 3–4 LLM calls per run

**Token Usage:**  
- Example run: Total calls: 3, Total tokens: ~1681  
- Cost: Minimal (well below $0.05 equivalent)

**Why Layer 2 vs Layer 3:**  
- Layer 1 → deterministic business rules  
- Layer 2 → numeric/statistical detection  
- Layer 3 → semantic reasoning only  

> I avoided sending structured numeric logic to LLM because it is expensive, slower, unnecessary, and reduces explainability. LLM was used only for semantic interpretation (HS classification, behavioral reasoning, executive summary).

---

## 4️⃣ Prompt That Didn’t Work and How I Fixed It

**❌ Bad Prompt:**  
> Is this HS code correct for the product?

**Problem:**  
- Returned long explanation text  
- Sometimes didn’t return JSON  
- No structured output  
- No severity level  

**✅ Improved Prompt:**  
Respond strictly in JSON:

```json
{
  "is_mismatch": true/false,
  "reason": "short explanation",
  "severity": "Low/Medium/High"
}
Enforced:
   response_format={"type": "json_object"}

Result:
   ·Structured output
   ·Deterministic parsing
   ·Reduced hallucination
   ·Reliable automation

Key lesson:
      Constrained JSON schema + system instruction significantly improved reliability.

## Precision and Recall

- **True Positives:** 11  
- **False Positives:** 0  
- **False Negatives:** 1  
- **Precision:** 1.0  
- **Recall:** 0.917  
- **Status:** Review Required

### Why False Negatives Occurred
- Some anomalies were close to the mean and not extreme enough  
- HS semantic ambiguity edge cases

### Notes
> Perfect precision indicates no false alarms, but a small number of false negatives remain. Review is recommended to ensure no critical anomalies were missed.

