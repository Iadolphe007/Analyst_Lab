**CONSUMER COMPLAINTS INTELLIGENCE**

**1. Project README**

**Project purpose**

This project analyses consumer complaints about financial products and services. It explores complaint volume and trends, product and issue patterns, company response outcomes, recorded timeliness and complaint-forwarding intervals.

**Project deliverables**

Cleaned Excel dataset with derived analysis fields.
Power BI dashboard with four pages: Executive Complaint Overview; Product and Issue Analysis; Company Response Analysis; Complaint Timeline Analysis.
Companion analysis summary with KPIs, business insights and recommendations.
 
**Dataset overview**

Attribute	                   Value
Rows	                       62,516
Date range	                   1 May 2017 – 28 August 2023
Unique key	                   Complaint ID
Granularity                    One complaint per record
Key fields	                   Date submitted, Date received, Product, Sub-product, Issue, State, company response, public response, timely response
Derived fields	               Year, Month number, Month, Quarter, Forwarding interval and updated response/timeliness fields

**Tools and workflow** 

Excel: data inspection, cleaning, derived columns, validation and exploratory summaries.
Power BI: measures, interactive visuals, filters and dashboard presentation.

**Dashboard guide**

Page	                            Purpose	             Core content

1. Executive Complaint Overview	    Executive snapshot   Total complaints, monthly trend, product distribution, timely-response percentage, average forwarding interval
2. Product and Issue Analysis	    Complaint drivers	 Complaints by product and sub-product, frequent issues, product-versus-issue matrix
3. Company Response Analysis	    Response outcomes	 Company response categories, Yes/No/Pending timeliness, in-progress complaints, public response categories
4. Complaint Timeline Analysis	    Timing and delays	 Monthly/annual trends, forwarding distribution, forwarding by product, unusually long intervals

**Refresh and reuse instructions**

Load the latest extract while preserving field meanings and data types.
Check that Complaint ID is populated and unique.
Validate both date fields and recalculate forwarding interval as Date received minus Date submitted.
Recheck missing values and category distributions after each refresh.
Refresh the Power BI model and reconcile KPI totals against the source.
Update the data cut-off date, row count and quality statistics in this document.

**2. Data-quality documentation**

**Important field definitions**

Field	                                                                  Meaning
Complaint ID	                                                          Unique complaint identifier used for distinct counts.
Date submitted	                                                          Date the CFPB received the complaint.
Date received	                                                          Date the complaint was sent/received by the company for this analysis.
Product / Sub-product	                                                  Financial product hierarchy.
Issue / Sub-issue	                                                      Consumer-reported problem classification.
Company response to consumer	                                          Company response outcome, including In progress.
Company public response	                                                  Public-response category recorded for the complaint.
Timely response?	                                                      Source timeliness field; updated analytical field used for dashboard reporting.
Forwarding interval	                                                      Calendar days between Date submitted and Date received.
Year / Month / Quarter	                                                  Derived calendar dimensions.

**Validation checks and results**
Check	                                        Observed result	                                       Treatment / interpretation
Record count	                                62,516	                                               Baseline row count for this extract.
Unique Complaint IDs	                        62,516 unique IDs	                                   No duplicate IDs identified.
Duplicate original rows	                        0 fully duplicated A: L rows identified	               No full-row duplicates identified in original fields.
Missing Complaint ID	                        0 reported	                                           Identifier completeness check passed.
Missing key dates	                            0 reported	                                           Date fields available for forwarding analysis.
Missing Product / Sub-product	                0 reported	                                           Core product grouping fields complete.
Missing Sub-issue	                            10,857 (17.37%)	                                       Do not infer from Product; retain as Not Provided/blank.
Missing Company public response	                2,175 (3.48%)	                                       Keep missing values explicit where category analysis requires it.
Missing Timely                                  response	1,494 (2.39%)	                           Updated analytically to Pending for in-progress cases.
Negative forwarding intervals	                0	                                                   No negative intervals identified.
Maximum forwarding interval	                    275 days	                                           Flag for record-level review; do not delete automatically.

**Cleaning and transformation decisions**

Area	                    Decision
Complaint ID	            Used as the unique record key; 62,516 unique IDs for 62,516 records.
Missing Sub-issue	        Not inferred from Product because a product can have multiple possible sub-issues. Use an explicit Not Provided label if needed in visuals.
Missing public response	    Do not invent a category; preserve missing values or label them Not Provided for display.
In-progress timeliness	    When Company response to consumer is In progress, Timely response updated is Pending. This is an analytical recoding.
Forwarding interval	        Calculated as Date received minus Date submitted in calendar days.
Long intervals	            Retain pending validation; flag values above 30 days for review.
Partial years	            2017 begins in May and 2023 ends in August; identify them as partial years.

**Known limitations**

The dataset ends on 28 August 2023 and is not a current feed.
2017 and 2023 are partial-year periods.
Missing Sub-issue values limit detailed sub-issue analysis.
Pending cases do not have a definitive timely/untimely outcome.
The 275-day maximum forwarding interval may be a genuine delay or a source-data issue; validate the record.
Complaint counts do not provide a denominator such as number of customers, accounts or transactions.
Recommended quality controls for future refreshes
Confirm Complaint ID is non-null and unique.
Confirm Date submitted and Date received are valid dates.
Check that Date received is not earlier than Date submitted; investigate negative differences.
Check category spelling and consistency for Product, Issue, company response and timeliness.
Report missingness percentages for all analytical fields.
Review new categories and unusually long forwarding intervals.
Reconcile total complaints and KPI numerators/denominators across Excel, SQL and Power BI.

**Interpretation safeguards**

Recorded timely-response rate = Yes / (Yes + No); Pending is excluded.
Report median alongside average forwarding interval because extreme values affect the mean.
Same-day forwarding means a zero-calendar-day difference, not necessarily processing within the same hour.
Company response-to-consumer and company public-response categories are separate fields.
Observed trends and associations do not prove causes.
Documentation note: these figures and decisions describe the project extract currently analyzed. Update the row count, date range, missingness figures and KPI values whenever the source dataset changes.

