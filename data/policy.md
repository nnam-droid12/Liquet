# Liquet Marketplace Dispute Resolution Policy

**Version 1.0 | Effective: 2025-01-01**

---

## Part I: General Principles

### P-001: Buyer Protection Standard
The marketplace provides buyer protection for purchases made through the platform. Buyers are entitled to remedies when an item is materially different from its listing, or when an item does not arrive.

### P-002: Seller Good Faith Standard
Sellers must accurately represent items, including condition, color, dimensions, and any defects. Intentional misrepresentation is a serious policy violation.

### P-003: Evidence Hierarchy
Evidence is weighted by reliability in this order:
1. Carrier scan records (highest — objective third-party data)
2. Platform order records
3. Original listing data (what was promised)
4. Buyer-submitted photos (credible if unedited, timestamped)
5. Seller-submitted photos
6. Message thread content
7. Unverified verbal claims (lowest)

### P-004: Non-Liquet Escalation
When the evidence does not clearly favor either party, or when a hard contradiction exists that cannot be resolved from available data, the case must be escalated to a human reviewer. An automated agent must not guess on genuinely uncertain cases.

---

## Part II: Dispute Types and Applicable Rules

### T-001: Item Not As Described

**Rule T-001-A (Color/Appearance Mismatch)**
If a buyer provides photographic evidence showing a material difference in color or appearance from the listing, and the listing photos show a clearly different appearance, a FULL REFUND is warranted.
- Threshold: difference must be material (e.g., "grey" vs "brown" is material; "slightly different shade" under different lighting is not).
- Seller's lighting defense is not sufficient without counter-evidence.

**Rule T-001-B (Condition Misrepresentation)**
If an item listed as "new" or "like new" arrives with damage not disclosed in the listing, the buyer is entitled to a FULL REFUND or REPLACEMENT at buyer's choice.
- If damage is minor and proportionate, a PARTIAL REFUND of 10–40% of order value may be offered.

**Rule T-001-C (Wrong Item Shipped)**
If the buyer receives a clearly different item from what was ordered (wrong model, wrong size category, wrong product), FULL REFUND or REPLACEMENT is warranted.

### T-002: Item Never Arrived

**Rule T-002-A (Carrier Confirms Non-Delivery)**
If the carrier tracking record shows no delivery scan, or shows an attempted delivery with no follow-up delivery, a FULL REFUND is warranted after a 7-day waiting period from estimated delivery date.

**Rule T-002-B (Carrier Confirms Delivery — Buyer Claims Non-Receipt)**
If the carrier confirms delivery with a signed receipt or GPS confirmation, the claim is significantly weakened. The agent may DENY the claim unless the buyer provides evidence of theft, wrong-address delivery, or other corroborating circumstances.

**Rule T-002-C (Tracking Stalled/Missing)**
If tracking shows in-transit status for more than 14 days beyond estimated delivery, the platform considers the package lost. FULL REFUND is warranted. The seller may pursue a carrier insurance claim.

### T-003: Item Arrived Damaged

**Rule T-003-A (Packaging Inadequate)**
If the buyer provides photographic evidence of damage AND the tracking record shows no special handling (or the item was fragile), the seller is responsible for inadequate packaging. FULL REFUND or REPLACEMENT is warranted.

**Rule T-003-B (Carrier Damage)**
If packaging shows external impact damage consistent with carrier mishandling, the seller should file a carrier insurance claim. The buyer receives a FULL REFUND. The seller is reimbursed through the insurance process.

**Rule T-003-C (Partial Damage)**
If only some items in a set are damaged, a PARTIAL REFUND proportional to the damaged fraction is appropriate.

### T-004: Counterfeit Item

**Rule T-004-A**
If photographic or expert evidence indicates counterfeit goods, FULL REFUND is mandatory regardless of order value. The case is flagged for seller account review.

---

## Part III: High-Value Order Rules

### V-001: Orders Above $500
All disputes involving orders above $500 USD require human review before resolution, regardless of confidence level. The agent must produce a complete decision brief and escalate.

### V-002: Partial Refund Calculation
For partial refunds, the refund percentage is:
- 25% for minor condition issues
- 50% for moderate issues (item usable but significantly impaired)
- 75% for severe issues (item barely usable)
- 100% for items that are unusable or completely as-described failures

---

## Part IV: Adjudication Constraints

### A-001: Confidence Threshold
The agent must not auto-resolve a case with confidence below 0.80. Low-confidence cases go to human review.

### A-002: Hard Contradictions
When there is a factual contradiction between evidence items that cannot be resolved (e.g., carrier says delivered, buyer provides credible delivery address evidence that it was delivered to the wrong address), the agent must escalate.

### A-003: Missing Critical Evidence
If critical evidence is missing (e.g., no tracking record exists, no listing photos exist) and the missing evidence would be decisive, confidence must be reduced accordingly and the case may escalate.

### A-004: Time Limits
Disputes must be filed within 30 days of delivery (or expected delivery). Disputes filed after this window are denied unless there is evidence of fraud.

---

## Part V: Resolution Actions

| Resolution | When Applied |
|---|---|
| FULL_REFUND | Item materially not as described, not arrived, or critically damaged |
| PARTIAL_REFUND | Partial damage or minor misrepresentation |
| REPLACEMENT | Buyer prefers replacement; seller is capable of providing one |
| RETURN_THEN_REFUND | High-value items where seller disputes damage claims |
| DENY | Insufficient evidence or buyer claim fails policy tests |
| ESCALATE | Case exceeds agent confidence or value thresholds |

---

*This policy is reasoned over by the Liquet policy engine during dispute adjudication.*
