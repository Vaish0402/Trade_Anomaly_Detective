**Summary of Anomalies for Leadership**

We have identified several anomalies across multiple shipments that require attention. These anomalies can be categorized into two main groups: Rule-Based and Statistical.

**Rule-Based Anomalies:**

1. **SHIP_1010**: A math error was detected in the shipment calculation, where the FOB (Free On Board) value does not match the expected calculation (395 * 11.42). Severity: High
2. **SHIP_1025**: An Incoterm violation was detected, where the freight cost is 0 despite the Incoterm being CIF (Cost, Insurance, and Freight). Severity: Medium

**Statistical Anomalies:**

Multiple shipments have unit prices that are significantly outside the expected bounds of [4.90, 6.10]. These outliers may indicate fraud or inefficiency and have a High severity level. The affected shipments are:

1. **SHIP_1010**: Unit price of 11.42
2. **SHIP_1025**: Unit price of 12.34
3. **SHIP_1050**: Unit price of 250.0
4. **SHIP_1075**: Unit price of 22.5

**Recommendations:**

1. Investigate the math error in SHIP_1010 to ensure accurate calculations.
2. Review the Incoterm violation in SHIP_1025 to ensure compliance with shipping regulations.
3. Further analyze the unit price outliers in all affected shipments to determine the cause and potential impact on the business.

By addressing these anomalies, we can ensure the accuracy and integrity of our shipping processes and prevent potential losses or inefficiencies.