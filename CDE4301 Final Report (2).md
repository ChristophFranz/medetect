<div align="center">
   
# CDE4301 Final Report
<div align="center">
<img width="700" height="700" alt="image" src="https://github.com/user-attachments/assets/0d2f5b9d-d5f5-4ffe-a502-3f04024dfb3d" />
<div align="center">

| Student Name | Student No. |
|--------------|------------|
|      Boh Jing Yi Celest        |    A0258279L        |
|         Ho Di En, Faith     |       A0258703B     |
|        Mathhias Khoo      |      A0253359X      |
|     Valerie Koh Ying Xuan     |      A0277975A    |

<div align="center">
   
__Supervisors__  
Mr Nicholas Chew

<div align="center">
   
__Word Count__  
11000
<div align="center">
   
## Acknowledgements

<div align="justify">

We would like to express our deepest gratitude to our supervisor, Mr Nicholas Chew for his invaluable guidance and support in the past semester. His vast experience and knowledge in optical imaging and innovation has helped us to think critically in our approach towards the problem and identify its underlying cause. His constant feedback during our weekly discussions has helped improve our thought processes and given us clarity in our project direction throughout the semester. He has also helped us to coordinate and liaise with personnel at the Singapore National Eye Centre (SNEC) allowing us to keep in touch with our key stakeholders who are crucial for our project.  
   
In addition, we would also like to thank Mr Jason, Ms Cynthia Wilson and the SNEC team for taking the time to discuss in great depth the problem we are working on. Finally, we extend our appreciation to Keyence for providing access to their imaging system, which was integral to our prototype development and overall project. 

<div align="center">
   
## Abstract
<div align="justify">
   
This report documents the development of *MEDetect*, an intelligent inspection system designed in collaboration with the Singapore National Eye Centre (SNEC) to improve the accuracy, consistency and efficiency of ophthalmic surgical tool inspections. The current manual inspection of approximately 17,000 surgical trays annually at SNEC is highly subjective, marked by significant inter-rater and intra-rater variability, particularly for tools like the Hook Sinsky and Forceps MacPherson. 

To address this challenge, *MEDetect* integrates high-resolution imaging (1.6M pixel) and AI-driven detection algorithms (YOLOv8) to enable precise and objective visual inspections. The system uses the Keyence VS-L160CX camera, selected for its ability to capture features as small as 0.2 mm based on preliminary analyses of critical tool tip diameters (0.18 - 0.42 mm). Its architecture features a specialised user workflow, including dual-layer scanning and a secondary-user login override to ensure accountability and data integrity. Prototyped using Lovable platform, the intuitive User Interface (UI) minimises manual input, providing clinical staff with clear 'Defective', 'OK' or 'Missing' status indicators. 

Ultimately, *MEDetect* represents a multidisciplinary approach to standardising surgical tool integrity and enhancing patient safety, with future work focusing on expanding the defect database and refining real-time integration for full operational deployment.

<div align="left">
<div id="list-of-tables">
  <h2>List of Tables</h2>
  <ul>
    <li><a href="#tab1">Table 1. Comparison of Inspection Methods</a></li>
    <li><a href="#tab2">Table 2. Design Specifications of Stakeholders</a></li>
    <li><a href="#tab3">Table 3. Functional Requirements of MEDetect</a></li>
    <li><a href="#tab4">Table 4. MEDetect Integrated System Components</a></li>
    <li><a href="#tab5">Table 5. Design Requirements for MEDetect User Interface</a></li>
    <li><a href="#tab6">Table 6. Prototype 1 Dataset Imaging Acquisition Conditions</a></li>
    <li><a href="#tab7">Table 7. Prototype 1 Iterations Dataset Training Configuration</a></li>
    <li><a href="#tab8">Table 8. Prototype 2 Version 1 And 2 Dataset Imaging Acquisition Conditions</a></li>
    <li><a href="#tab9">Table 9. Comparison Of Prototype 2 Version 1 And 2 Dataset Size, Dataset Split And Epoch Size</a></li>
    <li><a href="#tab10">Table 10. Summary Of The 5 Models Used In The Final System</a></li>
    <li><a href="#tab11">Table 11. Imaging Acquisition Conditions For Model 1</a></li>
    <li><a href="#tab12">Table 12. Model 2 Through 5 Imaging Acquisition Conditions</a></li>
    <li><a href="#tab13">Table 13. Annotated Images Of Defective And Non-Defective Tools</a></li>
    <li><a href="#tab14">Table 14. Summary Of Test Scenarios conducted on MEDetect's models</a></li>
    <li><a href="#tab15">Table 15. Test 1 Defect Identification Results</a></li>
    <li><a href="#tab16">Table 16. Test 2 Defect Detection Results</a></li>
    <li><a href="#tab17">Table 17. Test 3 Defect Detection Results</a></li>
    <li><a href="#tab18">Table 18. Test 4 Defect Detection Results</a></li>
    <li><a href="#tab19">Table 19. Test 5 Defect Detection Results</a></li>
    <li><a href="#tab20">Table 20. Wet/Dry: Tool Presence Detection Accuracy (%)</a></li>
    <li><a href="#tab21">Table 21. Wet/Dry: Tool Defect Identification Accuracy (%)</a></li>
    <li><a href="#tab22">Table 22. Wet/Dry: Tool Presence Detection Accuracy (%)</a></li>
    <li><a href="#tab23">Table 23. Wet/Dry: Tool Defect Identification Accuracy (%)</a></li>
    <li><a href="#tab24">Table 24. Underexposed Image vs Overexposed Image Used</a></li>
    <li><a href="#tab25">Table 25. Defect Identification Results</a></li>
    <li><a href="#tab26">Table 26. Rotation: Tool Presence Detection Accuracy (%)</a></li>
    <li><a href="#tab27">Table 27. Rotation: Tool Defect Identification Accuracy (%)</a></li>
    <li><a href="#tab28">Table 28. Overlapping of Trained Tools: Tool Presence Detection Accuracy (%)</a></li>
    <li><a href="#tab29">Table 29. Overlapping of Trained Tools: Defect Identification Accuracy (%)</a></li>
    <li><a href="#tab30">Table 30. Untrained Tools Used for Overlap Test</a></li>
    <li><a href="#tab31">Table 31. Overlap with Untrained Tools: Tool Presence Detection Accuracy (%)</a></li>
    <li><a href="#tab32">Table 32. Overlap with Untrained Tools: Defect Identification Accuracy (%)</a></li>
    <li><a href="#tab33">Table 33. Responses for Surgical Tool Integrity: Unique Images (Q1 - Q16)</a></li>
    <li><a href="#tab34">Table 34. Responses for Surgical Tool Integrity: Repeated Images (Q17 - Q24)</a></li>
    <li><a href="#tab35">Table 35. Summary of Responses Against Ground Truth</a></li>
    <li><a href="#tab36">Table 36. Response Distribution of Tool Classes (N= 18)</a></li>
    <li><a href="#tab37">Table 37. Images of tools with finest tips</a></li>
    <li><a href="#tab38">Table 38. Microscopic Images Of Ophthalmic Surgical Tool Tips</a></li>
    <li><a href="#tab39">Table 39. Microscopic Images Of Tools (Area Cropped For Measurement)</a></li>
    <li><a href="#tab40">Table 40. Concept Sketch Of The Final Assembly Vs Image Of Actual Set-Up</a></li>
    <li><a href="#tab41">Table 41. Concept Sketch of Profile Beam Assembly (CAD) vs Actual Profile Beam set-up</a></li>
    <li><a href="#tab42">Table 42. Concept Sketch of Profile Beam Design (CAD) and M6 Rhombus Nut Connection</a></li>
    <li><a href="#tab43">Table 43. Concept Sketch of Mounting Plate vs CAD Design of Mounting Plate</a></li>
    <li><a href="#tab44">Table 44. F1 Confidence Curve of Model 2 to 5</a></li>
    <li><a href="#tab45">Table 45. Precision Confidence Curve for Model 2 to 5</a></li>
    <li><a href="#tab46">Table 46. Precision Recall Curve for Model 2 to 5</a></li>
    <li><a href="#tab47">Table 47. Recall Confidence Curve of Model 2 to 5</a></li>
    <li><a href="#tab48">Table 48. Normalised Confusion Matrix for Model 2 to 5</a></li>
    <li><a href="#tab49">Table 49. Usability Survey Q1</a></li>
    <li><a href="#tab50">Table 50. Usability Survey Q2</a></li>
    <li><a href="#tab51">Table 51. Usability Survey Q3</a></li>
    <li><a href="#tab52">Table 52. Usability Survey Q4</a></li>
    <li><a href="#tab53">Table 53. Usability Survey Q5</a></li>
    <li><a href="#tab54">Table 54. Usability Survey Q6</a></li>
    <li><a href="#tab55">Table 55. Usability Survey Q7</a></li>
    <li><a href="#tab56">Table 56. Usability Survey Q8</a></li>
    <li><a href="#tab57">Table 57. Usability Survey Q9</a></li>
    <li><a href="#tab58">Table 58. Usability Survey Q10</a></li>
    <li><a href="#tab59">Table 59. Role and Responsibilities</a></li>
  </ul>
</div>

<div id="list-of-figures">
  <h2>List of Figures</h2>
  <ul>
    <li><a href="#fig1">Figure 1. AI-driven Quality Control in Manufacturing. (Gard, 2025).</a></li>
    <li><a href="#fig2">Figure 2. SNEC staff observing MEDetect prototype and interface during demonstration</a></li>
    <li><a href="#fig3">Figure 3. Surgical Tool Defects Assessment Results</a></li>
    <li><a href="#fig4">Figure 4. Stakeholder Power-Interest Matrix</a></li>
    <li><a href="#fig5">Figure 5. Image of the SUIS by Steelco Group</a></li>
    <li><a href="#fig6">Figure 6. Keyence VS Studio Interface</a></li>
    <li><a href="#fig7">Figure 7. MEDetect Physical Prototype</a></li>
    <li><a href="#fig8">Figure 8. System Wiring</a></li>
    <li><a href="#fig9">Figure 9. MEDetect System Physical Architecture and Interconnect</a></li>
    <li><a href="#fig10">Figure 10. User Process Flowchart</a></li>
    <li><a href="#fig11">Figure 11. Overall System Architecture Diagram</a></li>
    <li><a href="#fig12">Figure 12. Figma UI</a></li>
    <li><a href="#fig13">Figure 13. Comparison Between Conceptual Result Display In Figma And The Implemented Real-Time Result Cards</a></li>
    <li><a href="#fig14">Figure 14. System Integration Diagram Showing The API Communication Layer</a></li>
    <li><a href="#fig15">Figure 15. Lovable UI</a></li>
    <li><a href="#fig16">Figure 16. User Workflow</a></li>
    <li><a href="#fig17">Figure 17. User Authentication Via NFC Identification</a></li>
    <li><a href="#fig18">Figure 18. Dynamic Selection Panels</a></li>
    <li><a href="#fig19">Figure 19. UI Interface Of Both Direct And Manual Upload</a></li>
    <li><a href="#fig20">Figure 20. UI of Tray Analysis</a></li>
    <li><a href="#fig21">Figure 21. Manual Override</a></li>
    <li><a href="#fig22">Figure 22. Data Module And Case View</a></li>
    <li><a href="#fig23">Figure 23. Tool Classification Repository Interface</a></li>
    <li><a href="#fig24">Figure 24. Prototype 1 Dataset Images</a></li>
    <li><a href="#fig25">Figure 25. Prototype 1 Annotated Training Image (Roboflow)</a></li>
    <li><a href="#fig26">Figure 26. Detection results of Prototype 1 iterations</a></li>
    <li><a href="#fig27">Figure 27. Normalised Confusion Matrix (Prototype 1 Model)</a></li>
    <li><a href="#fig28">Figure 28. Image of CP (From Prototype 2 Dataset)</a></li>
    <li><a href="#fig29">Figure 29. Image of Labelled CP via Roboflow</a></li>
    <li><a href="#fig30">Figure 30. Normalised Confusion Matrix (Prototype 2 Version 1 Model)</a></li>
    <li><a href="#fig31">Figure 31. Detection Result Of Prototype 2 Version 1 (30 vs 60 Epochs)</a></li>
    <li><a href="#fig32">Figure 32. Normalised Confusion Matrix For Prototype 2 Version 2 Model</a></li>
    <li><a href="#fig33">Figure 33. Detection Result Of Prototype 2 Version 2 Model (Epoch Size 100)</a></li>
    <li><a href="#fig34">Figure 34. Images Examples From Varying Scenarios (Model 1)</a></li>
    <li><a href="#fig35">Figure 35. Labelling of 4 Main Tools (Model 1)</a></li>
    <li><a href="#fig36">Figure 36. Model 2 Through 5 Dataset Images</a></li>
    <li><a href="#fig37">Figure 37. Process Of Integrated Object Detection System</a></li>
    <li><a href="#fig38">Figure 38. Test 1 Tool Presence Detection Result</a></li>
    <li><a href="#fig39">Figure 39. Test 2 Tool Presence Detection Result</a></li>
    <li><a href="#fig40">Figure 40. Test 3 Tool Presence Detection Result</a></li>
    <li><a href="#fig41">Figure 41. Test 4 Tool Presence Detection Result</a></li>
    <li><a href="#fig42">Figure 42. Test 5 Tool Presence Detection Result</a></li>
    <li><a href="#fig43">Figure 43. Overall Model Performance: Presence vs Defect</a></li>
    <li><a href="#fig44">Figure 44. Brightness Auto Adjusted by KEYENCE Camera</a></li>
    <li><a href="#fig45">Figure 45. Image of Toolbox with Auto Adjusted Focus</a></li>
    <li><a href="#fig46">Figure 46. Blurred Image Of Toolbox</a></li>
    <li><a href="#fig47">Figure 47. Average Accuracy by Tool Type</a></li>
    <li><a href="#fig48">Figure 48. Accuracy by Scenario (Average)</a></li>
    <li><a href="#fig49">Figure 49. Overall Model Performance Comparison</a></li>
    <li><a href="#fig50">Figure 50. Overlap Test Of Trained Tools (HS And CP)</a></li>
    <li><a href="#fig51">Figure 51. Average Accuracy by Tool Type (Overlap)</a></li>
    <li><a href="#fig52">Figure 52. Accuracy by Scenario (Overlap)</a></li>
    <li><a href="#fig53">Figure 53. Overall Performance: Overlap of Trained Tools</a></li>
    <li><a href="#fig54">Figure 54. Overlap of Untrained Tools (FM and Repositor Iris)</a></li>
    <li><a href="#fig55">Figure 55. Average Accuracy by Tool Type (Untrained Overlap)</a></li>
    <li><a href="#fig56">Figure 56. Accuracy by Scenario (Untrained Overlap)</a></li>
    <li><a href="#fig57">Figure 57. Overall Performance: Overlap with Untrained Tools</a></li>
    <li><a href="#fig58">Figure 58. 3 Step Engineering Roadmap</a></li>
    <li><a href="#fig59">Figure 59. Years Of Surgical Tool Inspection</a></li>
    <li><a href="#fig60">Figure 60. Respondents’ Confidence in Assessment</a></li>
    <li><a href="#fig61">Figure 61. Factors Influencing Assessment</a></li>
    <li><a href="#fig62">Figure 62. Identified boundary and points on HS’s tip</a></li>
    <li><a href="#fig63">Figure 63. Image of Ronchi Slide (293 pixel)</a></li>
    <li><a href="#fig64">Figure 64. Identified boundary and points on CP’s tip</a></li>
    <li><a href="#fig65">Figure 65. Image of Ronchi Slide (438 and 443 pixels)</a></li>
    <li><a href="#fig66">Figure 66. Identified boundary and points on FMs tip</a></li>
    <li><a href="#fig67">Figure 67. Image of Ronchi Slide (97 and 128 pixels)</a></li>
    <li><a href="#fig68">Figure 68. Identified boundary and points on FU’s tip</a></li>
    <li><a href="#fig69">Figure 69. Image of Ronchi Slide (86 and 128 pixels)</a></li>
    <li><a href="#fig70">Figure 70. Boundaries and points on the FU tip</a></li>
    <li><a href="#fig71">Figure 71. Image of Ronchi Slide (89 pixels)</a></li>
    <li><a href="#fig72">Figure 72. Concept Iterations Of The Set-Up</a></li>
    <li><a href="#fig73">Figure 73. Image Of 1-Inch Profile Clamp</a></li>
    <li><a href="#fig74">Figure 74. Actual Mounting plate with Keyence Camera</a></li>
    <li><a href="#fig75">Figure 75. F1 Confidence Curve of Model 1</a></li>
    <li><a href="#fig76">Figure 76. Precision Confidence Curve of Model 1</a></li>
    <li><a href="#fig77">Figure 77. Precision-Recall Curve for Model 1</a></li>
    <li><a href="#fig78">Figure 78. Recall Confidence Curve for Model 1</a></li>
    <li><a href="#fig79">Figure 79. Normalised Confusion Matrix for Model 1</a></li>
    <li><a href="#fig80">Figure 80. Detection result of Prototype 2 Version 1 model with prediction confidence level set at 0.01230 (left), 0.012306 (middle), 0.01230 (right)</a></li>
    <li><a href="#fig81">Figure 81. Detection Result Of Prototype 2 Version 2’s Model Trained At Epoch Size of 60</a></li>
    <li><a href="#fig82">Figure 82. Normalised confusion matrix of Prototype 2 Version 2’s Model Trained At Epoch Size of 60</a></li>
    <li><a href="#fig83">Figure 83. Inventory of tools in a toolkit</a></li>
    <li><a href="#fig84">Figure 84. 1st layer of toolkit</a></li>
    <li><a href="#fig85">Figure 85. 2nd layer of toolkit</a></li>
  </ul>
</div>
<div align="center">
   
<a name="acronyms-table"></a>
### Acronyms

| Acronym | Definition |
| :--- | :--- |
| SNEC | Singapore National Eye Centre |
| CP | Chop Phaco |
| FM | Forceps Macpherson |
| FU | Forceps Utrata |
| HS | Hook Sinsky |
| TSSU | Theatre Sterile Supply Unit |
| UI | User Interface |
| YOLO | “You Only Look Once” (Object Detection Model) |

<div align="center">
   
# 1. Introduction
<div align="justify">

The inspection of ophthalmic surgical instruments is a critical safeguard for patient safety and procedural success. At SNEC, which performs approximately 17,000 cataract surgeries annually (SNEC, n.d.), scrub nurses must verify the integrity of instruments with tip diameters as small as 0.2 mm before and after every procedure. Although instruments are not replaced on a fixed schedule, they are changed individually and immediately upon the detection of a defect. Consequently, early and accurate identification is essential for maintaining high surgical standards.

Through site visits and interviews, the team identified that the manual inspection process, performed by approximately 30 - 35 scrub nurses who each conduct 4-5 inspections per shift, is heavily dependent on human intervention and judgment. This reliance introduces significant inspection variability among staff, influenced by factors like visual fatigue and subjective human judgment, which can lead to missed defects or unnecessary disposal of functional tools. 

This variability was quantified through a Surgical Tool Defects Assessment ([Appendix A](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-a-surgical-tool-defects-assessment)), which demonstrated significant inter-rater disagreement and high intra-rater uncertainty for tools like HS and FM. Furthermore, staff showed high subjective over-identification, resulting in 94 "Defective" responses for CP that had a known ground truth of only 3 defective units.

While automated inspection is widely used in other industries for quality control (Figure 1), its application to surgical tools remains limited due to their fine geometries, sterility requirements and varying material properties. In response, *MEDetect* was collaboratively developed with SNEC  as an intelligent system combining high-resolution imaging, computer vision and user-centred interface design for objective, standardised tool inspection.

<p align="center" id="fig1">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure1%20new.png" alt="Surgical Tool Defects Assessment Results" width="80%">
  <br>
  <i>Figure 1. AI-driven Quality Control in Manufacturing (Gard, 2025)</i>
</p>
<div align="center">

# 2. Problem Framing
<div align="left">
   
## 2.1 Need Statement

<div align="justify">

Post-procedure manual inspection of ophthalmic surgical tools is inherently subjective and highly inconsistent, as demonstrated by our assessment. Tool tips ranging from 0.18 - 0.42 mm ([Appendix B](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-b-microscopic-analysis-of-diameter)) often exceed the threshold of consistent human visual acuity of 0.0035 inches at a standard 12-inch viewing distance (Iowa State University, n.d.). Undetected tool defects that elude the naked eye such as micro-fractures and tip bending compromise surgical safety by increasing the risk of unintended tissue trauma or introducing microscopic foreign bodies into the ocular space (Deepak Care, 2025) during high-precision ophthalmologic procedures. Therefore, there is a critical need for a standardised, objective solution that reliably identifies these structural failures while integrating into the high-volume, high-pressure ophthalmology workflows.
<div align="left">

## 2.2 Clinical Assessment
<div align="justify">

To quantify the variability of inspection results among staff, a "Surgical Tool Defects Assessment" ([Appendix A](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-a-surgical-tool-defects-assessment)) was conducted with 18 staff nurses representing a diverse range of expertise, with half having more than 5 years of experience in surgical instrument inspection, ensuring that the findings reflect the challenges faced by even seasoned clinical professionals. Complementing this data-driven assessment, an on-site studio visit for SNEC staff to directly observe *MEDetect* was also organised (Figure 2).
<div align="left">
   
<p align="center">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/0465cb9ffa38709622a19dff3e58752626fb739a/Report%20Images/fig1.jpg"width="80%">
  <br>
  <i><span id="fig2">Figure 2. SNEC staff observing MEDetect prototype and interface during demonstration</i>
</p>
<div align="justify">

### 2.2.1 Methodology
<div align="justify">

Each respondent evaluated 24 images across four critical identified tool classes: Hook Sinsky (HS), Chop Phaco (CP), Forceps Macpherson (FM) and Forceps Utrata (FU). For each tool class, 108 total responses were recorded (18 participants × 6 images per tool class). Each set of six images consisted of four unique standardised images and two repeated images integrated into a randomised sequence to verify intra-rater consistency, ensuring that a nurse’s assessment of the same tool remained stable over time. Each image offered the options for "Defective", "Non-Defective" or "Unsure".
<div align="left">

### 2.2.2 Key Findings
<div align="justify">
The assessment recorded 108 total responses per tool class, revealing significant variability in human judgment (Figure 3). 

<p align="center">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/0465cb9ffa38709622a19dff3e58752626fb739a/Report%20Images/figure%201_survey%20assessment%20result.png" alt="Surgical Tool Defects Assessment Results" width="80%">
  <br>
  <i><span id="fig3">Figure 3. Surgical Tool Defects Assessment Results</i>
</p>
<div align="justify">
   
* **High Uncertainty:** HS and FM generated the highest number of "Unsure" responses (26 and 25 respectively), indicating that these geometries are the most difficult to evaluate even for experienced staff.
* **Subjective Over-Identification:** For CP, despite a ground truth of 3 defective tools, there were 94 "Defective" responses. This suggests a high rate of false positives where functional tools are likely flagged as defective due to subjective over-caution.
* **Low Consistency:** FM showed the most significant disagreement among participants, with a near-even split between "Defective" (45) and "Non-Defective" (38) judgments.

These findings demonstrate that manual inspection is highly inconsistent, influenced by external factors such as lighting conditions, surface reflections and viewing angles. The absence of a standardised and objective evaluation framework highlights a critical gap in current practices, thereby justifying the development of *MEDetect*.

By mapping stakeholders based on their influence (Power) and engagement level (Interest), the Power–Interest Matrix in Figure 4 identifies Inspection Nurses and Nurse Managers as key stakeholders within the “Manage Closely” quadrant. Their high level of involvement in daily operations makes them critical to the system’s success, justifying *MEDetect*’s emphasis on reducing inspection variability through a simple and intuitive user interface.

Meanwhile, Hospital Administration falls within the “Keep Satisfied” quadrant, influencing requirements related to accountability, compliance, and auditability. To address these needs, the system incorporates features such as a dual-login override mechanism and automated traceability reports. This ensures that the final design not only supports frontline clinical usability but also aligns with broader organisational and regulatory requirements.

<p align="center" id="fig4">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure2_powermatrix.png" width="80%">
  <br>
  <i>Figure 4. Stakeholder Power-Interest Matrix</i>
</p>
<div align="justify">

## 2.3 Value Proposition 
<div align="justify">

The primary value of the system lies in its ability to standardise the detection and identification of microscopic defects, ensuring that only functioning surgical tools reach the operating table, ensuring patient safety. 

This project focuses on four of the finest surgical tools ("HS", "CP", "FM" and "FU") commonly used by SNEC. 

**Tools *MEDetect* focuses on:**

<p align="center">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tools.png" width="80%">
  <br>
</p>
<div align="justify">
   
These four tools were strategically selected as "corner-case" benchmarks to stress-test the system’s machine learning against the most extreme geometric boundaries in the toolkit. 

<div align="left">
   
The technical rationale is twofold:
<div align="justify">

1. **Resolution Thresholds**: These tools feature the finest tip diameters ranging from 0.18 mm to 0.42 mm ([Appendix B](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-b-microscopic-analysis-of-diameter)). If the system can reliably resolve defects at this sub-millimeter scale, it possesses the native resolution to detect anomalies on the other less complex tools in the same toolkit ([Appendix I](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-i-comprehensive-inventory-of-ophthalmic-surgical-tools)).
<div align="justify">
   
2. **Classification Ambiguity**: The selection includes pairs with high geometric similarity, specifically the FM/FU pair and CP/HS pair. Successfully training the system to distinguish between these nearly identical silhouettes ensures that it will be capable of identifying minute, distinct structural differences that often elude human staff.

Hence, by validating against these extreme geometries, *MEDetect*’s data architecture provides a scalable foundation for future enhancements to expand the system detection model to cover other tools with geometries no finer than the four tools identified in our project.  

This scalability ensures that *MEDetect* remains a future-proof solution, capable of evolving alongside the increasing volume of ophthalmological surgeries and growing operational needs of SNEC. Ultimately, *MEDetect* supports standardised and objective tool inspection by providing a reliable, traceable and easy-to-use platform that strengthens confidence in surgical tool inspection.
<div align="left">

## 2.4 Existing Solutions
<div align="justify">
Current market solutions for surgical instrument inspection generally focus on logistical efficiency and inventory management rather than the microscopic integrity of the tools themselves. An example is the Surgical Instrument Utility System (SUIS) by the Steelco Group (Figure 5), which utilises computer vision and RFID integration to automate the identification and counting of instruments (Steelco S.p.A., 2024). In these systems, RFID serves as a tracking technology that uses radio waves to identify tagged items, simplifying asset management and tray preparation.

<p align="center" id="fig5">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure3_suis.png" width="80%">
  <br>
  <i>Figure 5: Image of the SUIS by Steelco Group</i>
</p
<div align="justify">

While effective for tray preparation and asset tracking in large-scale sterile reprocessing units, these systems present several critical gaps for ophthalmic applications:

* **Logistical versus Integrity Focus:** Existing systems prioritise inventory counting and tracking rather than the detailed assessment of tool integrity required for surgical safety.
* **Resolution Constraints:** They are not designed to detect the fine-grained defects occurring on ophthalmic tips as small as 0.2 mm in diameter.
* **Spatial and Environmental Requirements:** These solutions often require substantial floor space, making them unsuitable for the compact and highly specialised environment of the TSSU (Theatre Sterile Supply Unit).
* **High Complexity and Cost:** The infrastructure required for RFID tagging and large-scale vision integration demands significant capital investment and technical oversight, which is often impractical for specialised eye centers.

Consequently, there remains a significant unmet need for a high-resolution, compact inspection solution capable of identifying minute defects while fitting seamlessly into existing clinical workflows.
<div align="left">
   
## 2.5. Comparative Analysis of Inspection Methods
<div align="justify">
   
To further define the project’s scope, *MEDetect* was evaluated against current clinical standards and traditional industrial automation (Table 1). 

<p align="center" id="tab1">
   <i>Table 1. Comparison of Inspection Methods</i>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/0465cb9ffa38709622a19dff3e58752626fb739a/Report%20Images/table1_new.png" width="80%">
</p>
   
<div align="justify">
   
While manual inspection remains the current standard, it is hindered by subjectivity and visual fatigue, leading to inconsistent results. Data from our clinical assessment ([Appendix A](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-a-surgical-tool-defects-assessment)) indicates a profound lack of consensus between nurses. For instance, when evaluating FM, judgments were closely split, with 45 respondents identifying a tool image as "Defective" while 38 identified the same image as "Non-Defective". Individual judgment is similarly volatile, most evidently for HS where 13 out of 18 respondents reversed their initial classification when unknowingly presented with the same tool image a second time. These results confirm that manual inspection is highly susceptible to external factors such as lighting, surface reflections and viewing angles, rather than objective criteria. 

Conversely, standard off-the-shelf industrial vision systems (ie. a standalone Keyence setup), while fast, often lack the specialised flexibility required for varied, fine-geometry surgical tools. A key limitation of traditional inspection systems lies in their reliance on predefined detection regions and rigid pixel-based constraints. These systems typically require staff to manually position the surgical tool within a fixed field of view or bounding box prior to inspection. As a result, any deviation in tool placement such as misalignment or positioning outside the predefined region can lead to failed or missed detections.

Furthermore, detection performance is constrained by the fixed resolution of the imaging hardware (ie. 1440 x 1072 pixels in systems like the Keyence VS-L160CX), limiting the system’s ability to accurately capture and analyse fine tool tip features. This combination of manual dependency and resolution constraints reduces robustness and reliability in real-world clinical workflows.

Designed for backend engineers rather than clinical staff, navigating the Keyence VS Studio interface (Keyence, n.d.) (Figure 6) is impractical in a high-pressure, fast-paced sterile processing environment. 

<p align="center" id="fig6">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%204.png" width="80%">
  <br>
  <i>Figure 6: Keyence VS Studio Interface </i>
</p>
<div align="justify">
   
Thus, *MEDetect* is engineered as an all-in-one visual inspection solution that combines high resolution imaging capabilities of the Keyence camera and a user-friendly user interface for seamless clinical workflow integration, requiring minimal user interactions while producing meaningful detection output.

<div align="center">

# 3. System Design
<div align="justify">
   
The design requirements for *MEDetect* were developed through clinical observations, stakeholder interviews and literature review, translating user needs into measurable engineering specifications.
<div align="left">
   
## 3.1 Design Specifications
<div align="justify">
   
The design specifications, in Table 2, reflect the operational needs expressed by SNEC stakeholders and define clear performance expectations for *MEDetect*. These needs were prioritized using an internal criteria-ranking matrix that evaluated clinical risk, frequency of occurrence and workflow impact. 

As a result, specifications related to visual accuracy, tool counting reliability and defect detection were ranked as highest priority because they directly influence patient safety and inspection consistency.

Operational requirements such as staff accountability, inspection time and portability were subsequently prioritised as they affect day-to-day usability and deployment feasibility within SNEC.

<p align="center" id="tab2">
   <i>Table 2. Design Specifications of Stakeholders</i>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table2.png" width="80%">
</p
<div align="left">

## 3.2. Functional Specifications 
<div align="justify">
   
Building upon the design specifications, the functional requirements (Table 3) define the essential behaviors and capabilities *MEDetect* must demonstrate. These requirements translate user expectations into actionable engineering functions that guide development and future performance evaluation.

<p align="center" id="tab3">
   <i>Table 3. Functional Requirements of MEDetect</i>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table3.png" width="80%">
</p
<div align="justify">
   
In addition to these requirements, preliminary measurements of tool tip diameter and curvature were conducted to establish baseline reference profiles. These measurements validated the necessity for a minimum resolvable feature size of approximately 0.18 - 0.20 mm ([Appendix B](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-b-microscopic-analysis-of-diameter)).
<div align="left">
   
## 3.3 System Configuration
<div align="justify">
   
The *MEDetect* system integrates specialised hardware and supervised machine learning to perform objective and rigorous inspection of ophthalmic surgical instruments. 
<div align="left">

### 3.3.1 Physical Prototype Assembly
<div align="justify">

Initial phases of the project focused on enginering a physical prototype (Figure 7) capable of providing optimal image acquisition, essential for consistent detection. It features a modular workstation consisting of a clamping mount that can be integrated into existing hospital trolleys, facilitating seamless adoption into the clinical environment.

The assembly comprised three primary hardware elements:

1. **Imaging Hardware:** A Keyence VS-L160CX camera mounted via an inverted L-beam and adjustable mounting clamp to ensure a fixed, top-down perspective of the instrument trays.
2. **Infrastructure:** The inverted L-beam configuration provides the necessary field of view and stability for high-resolution image acquisition.
3. **Power Management:** A portable DC power supply allows the system to operate across different areas of the surgical suite.

<p align="center" id="fig7">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/setup.jpg" width="50%">
  <br>
  <i>Figure 7. MEDetect Physical Prototype</i>
</p>
<div align="justify">   
   
This physical foundation ([Appendix C](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-c-physical-prototyping-and-hardware-assembly)) successfully demonstrated the feasibility of automated imaging, providing the high-quality data necessary to support subsequent computer vision development.
<div align="left">   

### 3.3.2 Functional Integration 
<div align="justify">   
   
Table 4 consolidates the hardware and software layers that form the *MEDetect* pipeline.

<p align="center" id="tab4">
  <i>Table 4. MEDetect Integrated System Components</i><br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/f2006fa5303237cafd1e3dd0169b12b95b20790d/Report%20Images/table4.png" width="80%">
</p>
<div align="justify">   

The hardware layer facilitates the initial capture of raw data, while the software layer executes the critical tasks of image processing, tool segmentation, defect classification and result visualisation. By consolidating these functions into a single pipeline (Figure 8), *MEDetect* minimises the subjectivity and inconsistency inherent in manual inspection. This integration transforms raw imaging data into a reliable, objective alternative that standardises tool inspection across high-volume clinical workflows.

<p align="center" id="fig8">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/9a2d27ff5647fd6a5dffbb280ab22c25353538a8/Report%20Images/figure5.png" width="80%">
  <br>
  <i>Figure 8. System Wiring</i>
</p>
<div align="left">   

The physical integration of the MEDetect system is centered on a high-speed hardware-to-software interconnect, as illustrated in Figure 9.

<p align="center" id="fig9">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/d6ddb0d29276b7cf03dcd337299e04e53d3832f5/Report%20Images/fig2setup.png" width="80%">
  <br>
  <i>Figure 9. MEDetect System Physical Architecture and Interconnect</i>
</p
<div align="left">   

## 3.4 User Workflow
<div align="justify">   
   
To ensure fast and consistent inspections with minimal manual intervention, the *MEDetect* workflow follows a structured sequence (Figure 10).

<p align="center" id="fig10">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure6.png" width="80%">
  <br>
  <i>Figure 10. User Process Flowchart</i>
</p>
<div align="justify">

This automated workflow significantly reduces the physical demand on inspection staff while eliminating the inconsistencies inherent in human-led assessments.
<div align="center">   
   
# 4. Concept Design
<div align="left">

## 4.1 User-Centric Interface Concept
<div align="justify">   

The *MEDetect* interface was developed with reference to the ISO 9241-210:2019 (ISO, 2019) human-centered design framework, ensuring that the design process is driven by an explicit understanding of users, tasks and environments while addressing the variability identified. The interface was initially conceptualised using Figma, a design tool that creates high-fidelity UI mockups for testing user workflows and prioritising cognitive ease before technical implementation.

To ensure the system is intuitive for clinical staff with minimal training, the design focuses on:

* **Visual Hierarchy:** Following Nielsen’s 1st Heuristic - Visibility of System Status (Nielsen, 1994), results on the UI are semantically displayed using standardised status labels, allowing for the instantaneous identification of 'Defective', 'OK' or 'Missing' tools.
* **Workflow Integration:** Guided by Hick’s Law which states that the time required to make a decision increases with the complexity of choices (Yablonski, n.d.), the UI minimises manual input and only requires a limited number of interactions from initial authentication to final report generation.
* **Diagnostic Clarity:** Leveraging Nielsen’s 5th Heuristic - Error Prevention (Nielsen, 1994), the UI presents large, clear visual confirmations for tool integrity checks, specifically targeting the 0.2 mm microscopic defects that are notoriously difficult to detect with the naked eye.
<div align="left">

## 4.2 Modular Inspection Concept
<div align="justify">

The core intelligence of *MEDetect* is structured as a multi-stage automated pipeline. This modular architecture allows the system to handle the complex task of identifying tool presence and tool tip defects.

The pipeline operates in two distinct stages:

* **Stage 1 - Tool Presence Detection:** The system first identifies tool presence and localises coordinates of the four target tool classes (HS, CP, FM, and FU) within the toolbox regardless of tool orientation.
*  **Stage 2 - Defect Identification:** Detected tools are automatically cropped into individual images and processed through tool-specific defect identification models. These models are trained to recognise defects like tip breakage or bending. 

By separating tool presence detection and defect identification, *MEDetect* allows for specialised accuracy for fine geometries while ensuring processing efficiency required for high-volume clinical tray checks. 
<div align="center">   

# 5. User Interface Design and System Integration
<div align="justify">   

The *MEDetect* user interface was developed to operate as the integration layer that connects the computer vision detection pipeline, inspection hardware and case documentation system into a cohesive platform for surgical tool verification. While the detection model performs automated instrument detection and defect identification, the interface acts as the bridge between system users and the detection capabilities, enabling the system to function within a practical clinical workflow by providing the interaction layer through which users capture images, review analysis results and document inspection outcomes.

In surgical environments, surgical instruments must be inspected carefully to ensure that all tools are present and in acceptable condition prior to and after procedures. Traditionally, this process is performed manually by staff nurses, which introduces potential risks associated with human error, fatigue, and limited traceability of inspection decisions. The *MEDetect* interface was therefore designed to augment this process by providing an operational platform that supports automated tool detection while maintaining human oversight and accountability within the workflow.

Rather than functioning solely as a visualisation layer for machine learning results, the interface acts as the coordinating system that links multiple components including the inspection camera, the detection model and the inspection database. Through this, the interface enables real-time inspection, structured documentation of results, and the collection of labelled tool images that may be used to improve the detection model over time. In doing so, the user interface transforms the detection model from a standalone analytical component into a deployable inspection support system capable of assisting healthcare professionals during surgical instrument verification.

<div align="left">   

## 5.1 UI/UX Design Objectives and Requirements
<div align="justify">   

The design of the *MEDetect* user interface was guided by the operational workflow of surgical instrument preparation and verification within clinical environments. In hospital settings, instrument trays must be inspected under strict procedural accuracy. Consequently, the interface must support efficient interaction while ensuring that inspection results remain clearly interpretable and traceable. 

To achieve this, several design requirements were established to guide the development of the interface. These requirements were informed by user-centered design principles which emphasises designing systems around the needs, capabilities and limitations of end users as well as establish simplified usability strategies for users. These strategies include minimising cognitive load and supporting clear system feedback.

These requirements *(Table 5)* were derived from the functional needs of surgical staff as well as the technical constraints of integrating computer vision analysis into a clinical workflow.

<p align="center"id="tab5">
  <i>Table 5: Design Requirements for MEDetect User Interface</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%206.png" width="80%">
</p>

The design requirements outlined above guided the development of the *MEDetect* interface and influenced both the structure of the inspection workflow and the supporting database architecture. By prioritizing usability, accountability, and integration with automated analysis, the interface enables computer vision-based inspection to be incorporated into the surgical instrument inspection process while maintaining human oversight and operational transparency.

<div align="left">   

## 5.2. System Architecture
<div align="justify">   
   
The *MEDetect* system adopts a modular architecture *(Figure 11)* designed to integrate the inspection interface, computer vision detection pipeline, hardware components, and case management infrastructure into a unified inspection platform. This architecture separates system responsibilities into multiple functional layers, allowing each subsystem to operate independently while maintaining structured communication between components.

<p align="center" id="fig11">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/System%20Integration%20Diagram.png" width="80%">
  <br>
  <i>Figure 11. Overall System Architecture Diagram </i>
  </p>
<div align="justify">   

At the user interaction layer, the interface is implemented as a web-based application using modern frontend technologies (React with TypeScript), enabling a responsive and modular design suitable for integration with real-time detection outputs and backend services which is suitable for clinical workstation environments. This interface serves as the primary interaction point through which users initiate inspections, review detection results, and access stored inspection records.

The backend infrastructure is hosted using Lovable Cloud services, a cloud-based development platform that provides integrated backend capabilities including database management, serverless edge functions, and object storage.

Within the *MEDetect* system, these backend services support core operational requirements like user authentication, role-based access control, case storage, and retrieval of inspection data. The execution of server-side logic such as verifying user permissions, saving inspection cases, and managing status overrides during tool verification are also possible through the serverless edge functions of Lovable Cloud services.

Automated instrument detection is performed through an external computer vision analysis server implemented in Python. The detection pipeline processes captured images of surgical instrument trays and returns structured analysis results that include detected tool classes, tool counts, and defect status information. Communication between the interface and the detection pipeline is facilitated through an application programming interface (API) layer that enables captured images to be transmitted to the detection server for analysis.

At the hardware level, the system integrates with an industrial Keyence IP camera used to capture high-resolution images of surgical instrument trays. The interface supports both direct image capture from the camera as well as manual image upload as a fallback mechanism during development or testing. Once an image is captured, it is transmitted to the detection server for processing before the resulting analysis data is returned to the interface for visualization and verification.

The overall system architecture enables the interface to coordinate interactions between hardware inputs, machine learning analysis, and database storage. By separating the user interface, backend services, and detection pipeline into modular components, the system maintains flexibility and allows individual subsystems to be updated or improved without requiring extensive modifications to the entire platform.
<div align="left">   

## 5.3 Iterative Development Process
<div align="justify">   
   
The development of the *MEDetect* user interface followed an iterative design and prototyping process where earlier versions of the system were refined based on both technical constraints and workflow considerations. Rather than implementing the full system architecture in a single stage, the process emphasised identifying key usability and workflow requirements that are crucial for clinical adoption.
<div align="left">   

### 5.3.1 Initial Conceptual Interface (Figma)
<div align="justify">   
   
The primary objective of this early stage was to explore how key system components (Figure 12), which included the camera feed, inspection controls and detection results, could be structured within a single interface. To fulfill some of the design objectives and requirements, the design focused on minimising interface complexity while ensuring that inspection results could be easily interpreted at a glance by users performing the tasks.

<p align="center" id="fig12">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/Figma%20UI.gif" width="80%">
  <br>
  <i>Figure 12: Figma UI</i>
  </p>
<div align="justify">

However, this initial prototype was limited to a static representation of the workflow (Figure 13). The functional elements such as real-time camera integration, automated detection results and database connectivity were not yet incorporated.

<p align="center" id="fig13">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig11_new.png" width="80%">
  <br>
  <i>Figure 13.Comparison Between Conceptual Result Display In Figma And The Implemented Real-Time Result Cards Showing Tool Classification</i>
  </p>
<div align="left">

### 5.3.2 Key Design Learnings from Initial Iteration
<div align="justify">
   
During the transition from conceptual to functional, several important requirements that were not fully apparent were revealed.

Firstly, real-time integration between system components was critical. While the Figma mockups successfully illustrated the intended layout, they did not account for the complexity of integrating the live camera feeds and automated detection outputs. This highlighted the need for a system architecture (Figure 14) capable of supporting real-time data flow between the interface and the detection pipeline.

<p align="center" id="fig14">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2011.png" width="80%">
  <br>
  <i>Figure 14: System integration diagram showing the API communication layer connecting the interface to the Python detection server.</i>
  </p>
  
<div align="justify">
   
Secondly, it became apparent that dynamic result visualisation was necessary to support rapid decision-making. The static representations of detect results were insufficient for clinical users which required immediate and clear feedback on tool status which led us to the development of structured result panels and visual indicators in the implemented system.

Lastly, the importance of workflow compatibility during implementation where the interface needed to guide users through a structured workflow rather than simply displaying information due to the inherent multi-step nature of the inspection process.
<div align="left">

### 5.3.3 Final Interface Implementation
<div align="justify">
   
Building on the earlier insights, the final *MEDetect* interface shown in Figure 15 was therefore developed with all the above functional system components like real-time imaging and automated detection results.

<p align="center" id="fig15">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/Lovable%20UI.gif" width="80%">
  <br>
  <i>Figure 15. Lovable UI</i>
</p>
<div align="left">    

## 5.4 Inspection Workflow Implementation
<div align="justify">   
   
Developed and structured to align with existing inspection procedures, *MEDetect* is designed to support the verification of surgical instrument trays performed by nurses or sterile processing staff. The inspection process consists of several sequential stages (Figure 16) including user authentication, inspection initialisation, image capture, automated analysis and case documentation. Each stage is designed to guide the user through the verification process while ensuring that inspection results remain clearly visible and traceable.

<p align="center" id="fig16">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure13.png" width="80%">
  <br>
  <i>Figure 16. User Workflow</i>
  </p>
<div align="left">
   
### 5.4.1 User Authentication
<div align="justify">
   
The workflow begins with user authentication using an NFC-based identification system to allow rapid user identification while reducing interaction complexity. The scanned NFC tag ID is verified against the system database to identify the user and retrieve their associated access permissions (Figure 17a and Figure 17b).

<p align="center" id="fig17">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig%2014.png" width="80%">
  <br>
  <i>Figure 17a (Left) and 17b (Right): User Authentication Via NFC Identification</i>
  </p>
<div align="left">

### 5.4.2 Selection Panel
<div align="justify">

Once authenticated, users are presented with a selection interface that acts as the central navigation hub of the application. It provides two primary modules of the system; the inspection module, and the database module.

Depending on the authenticated user’s access permissions, the interface will dynamically display available options. Nurses can access both the inspection workflow and the case database (Figure 18a), while administrators have additional access to the tool classification repository found in the database, user management functions but not the inspection system (Figure 18b).

<p align="center" id="fig18">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2015.png" width="80%">
  <br>
  <i>Figure 18a (left) and 18b (right): Dynamic Selection Panels</i>
  </p>
<div align="left">

### 5.4.3 Inspection Interface
<div align="justify">
   
Once selected, the user is guided through the tray inspection workflow. The inspection interface is designed to present the camera feed, capture controls, the analysis results within a single view to minimize navigation between different interface elements. 

<p align="center" id="fig19">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2016.png" width="80%">
  <br>
  <i>Figure 19a (Left) And 19b (Right): UI Interface Of Both Direct And Manual Upload</i>
  </p>
<div align="justify">
   
The interface supports two image acquisition methods:

* 1. Direct image capture from the connected keyence camera via ethernet cable (Figure 19a)
* 2. Manual image upload as a fallback mechanism (Figure 19b)

Once an image is captured or uploaded, the results are transmitted to the detection server for analysis.
<div align="left">

### 5.4.4 Automated Analysis and Result Visualisation
<div align="justify">

Once transmitted to the server for automated analysis, the model identifies the surgical tools present in the image and determines their defect status. More information on the model can be found in the following segment of the report. The resulting analysis is returned to the UI in a structured format that includes the detected tool name, tool counts, and defect classification.

The interface (Figure 20) displays these results through a visual panel that highlights the status of each detected tool. The annotated images generated by the detection pipeline are also displayed to provide visual confirmation of the detection results.

<p align="center" id="fig20">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/Fully%20Analysed%20UI.gif" width="80%">
  <br>
  <i>Figure 20: UI of Tray Analysis</i>
  </p>
<div align="left">

### 5.4.5 Manual Classification Override
<div align="justify">

Although the detection models provide automated classification and detection of each tool’s integrity results, users retain the ability to modify the classification outcomes if necessary. This functionality is important in cases where the automated detection may misclassify tools due to variation in lighting, tool orientation or occlusion.

When a user attempts to change a classification result, the system (Figure 21) requires confirmation from a second authenticated user through an NFC verification process. This verification mechanism ensures that classification modifications are validated by multiple users, maintaining accountability within the inspection process. 

<p align="center" id="fig21">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/manual%20override.gif" width="80%">
  <br>
  <i>Figure 21: Manual Overide</i>
  </p>
<div align="left">

### 5.4.6 Case Documentation and Storage
<div align="justify">

After the inspection process is completed, the system automatically generates an inspection record that includes the captured images, annotated detection results, and associated metadata such as the inspection time and responsible users.

These cases are stored in the system database allowing users to review past inspections, retrieve case reports and download documentation when required providing traceability for verification activities.
<div align="left">

## 5.5 Case Management and Data Infrastructure
<div align="justify">

In addition to storing inspection records, the database interface provides a system that presents the inspection cases in a searchable and filterable list. Users can locate specific cases using multiple filtering criteria such as patient identifier, inspection date or the user who performed the inspection allowing users to efficiently navigate a large repository of inspection records.

The interface also highlights cases in which tool classifications have been manually modified through the override mechanism in the form of a pulsating orange orb (Figure 22a). When a case is selected from the database (Figure 22b), the system presents a detailed case view that allows users to examine the results of inspection in greater depth by displaying both the original captured image and annotated detection outputs generated by the computer vision model.

<table id="fig22">
  <tr>
    <td><img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2019.png?raw=true" width="80%"></td>
    <td><img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/case%20view.gif?raw=true" width="150%"></td>
  </tr>
  </tr>
</table>
<div align="center">
   
*Figure 22a (left) And 22b (right): Data Module And Case View* 

<div align="left">

### 5.5.1 Tool Classification Repository
<div align="justify">

The tool classification repository (Figure 23a-d) is a hidden repository designed to store cropped images of individual surgical instruments extracted during the detection process. These images are automatically generated by the detection pipeline during inspection and organised by instrument type within the system.

Access to this repository is restricted to users with the “Administrator” user role where unlike the general case database, which is accessible to inspection staff for reviewing completed inspections, the repository is intended for administrative review and dataset management. Restricting the access ensures that classification data used for model refinement remains controlled and consistent.

<div align="center">

<table id="fig23">
  <tr>
    <td><img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/1.png" width="100%"></td>
    <td><img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/2.png" width="100%"></td>
  <tr>
  <tr>
    <td><img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/3.png" width="100%"></td>
    <td><img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/4.gif" width="100%"></td>
  </tr>
  </tr>
</table>
<div align="center">

*Figure 23a (Top Left), 23b (Top Right), 23c (Bottom Left), 23d (Bottom Right): Tool Classification Repository Interface Showing Tool Images With Classification Status Indicators*

<div align="left">

### 5.5.2 Continuous Model Improvement
<div align="justify">

The integration of the repository introduces an important capability for continuous model improvement. Machine learning systems benefit from access to labelled datasets that reflect real-world operating conditions and by embedding the dataset collection directly into the inspection workflow, *MEDetect* allows labelled tool images to be gathered automatically during routine use of the system.

This approach reduces the need for separate data collection efforts while ensuring that the dataset reflects the variability of real surgical tool inspection environments. Over time, we hope that the accumulation of additional labelled examples can be used to refine the detection model and improve its robustness with the everchanging medical field.

<div align="center">

# 6. Object Detection Model
<div align="left">

## 6.1 Object Detection Objectives
<div align="justify">
   
The inspection process of instruments is crucial to ensure tools used for surgical procedures are safe for patients. But the current manual inspection process is prone to significant variability, as it relies heavily on subjective human judgment. Furthermore, performing repetitive inspections across multiple staff members introduces visual fatigue, leading to inconsistent results. To mitigate these issues, implementing a computer vision model for object detection ensures consistency and minimizes human variability.

*MEDetect* provides a multi-level object detection system by integrating five different models. One model performs tool presence detection of the four tools (CP, FM, FU, HS) and the other four models, each respective to the individual tool will detect whether the tools are defective or non-defective.
<div align="left">

## 6.2 Object Detection Model Selection
<div align="justify">
   
*MEDetect* uses YOLOv8 for object detection as it ensures high accuracy, speed and performance (Ultralytics, 2023). YOLOv8 is a widely used version with a large support system that has extensive tutorial and community resources (Ultralytics, n.d). Moreover, this version offers a variety of computer vision tasks not limited to object detection but also instance segmentation and more. In the future, if more complex computer vision tasks are needed for the project, this version is compatible.
<div align="left">

## 6.3 Object Detection Prototype Training Methodology
<div align="justify">

In this project two prototypes were developed, tested and analysed before finally leading to the development of *MEDetect's* Object Detection System. Data acquisition for all models for the prototypes and final system have a similar overall arching model training methodology. 

Images were first acquired using the Keyence camera, and were captured under various placement, lighting, orientation and background. Diverse images are crucial as it allows the model to learn a variety of situations allowing it to likely perform well with real-world scenarios. This is because with different variation in images, detection difficulty increases providing a reliable assessment of the model performance in actual applications (He et al, 2025)

Subsequently, the images are uploaded into Roboflow, a free labelling software compatible with YOLOv8. The images were manually labelled to classify the respective object to their distinct classes.

After manual labelling was completed, the dataset was split into three groups, Training, Validation and Testing. The ratio for split usually constitutes 70-80% of data to Training and 20-30% to Validation and Testing. The training dataset contributes to a larger portion to allow the model to understand patterns, while the testing dataset is used to evaluate the performance of the trained model (Sivakumar, 2024). Based on the study results conducted by Sivakumar et al. (2024), the data split ratio of 75:25 had relatively better performance and accuracy specifically for both logistic regression and random forest. In this project, the analysis of the study excluded 90:10 ratio and above, as *MEDetect's*’ training dataset size was too small, and a 90:10 ratio would lead to insufficient Validation and Testing Dataset. 

In this project, a 75% Training to 25% Validation and Testing split was utilised to train the *MEDetect* object detection models. And the respective datasets ran through YOLOv8 to create the customised models for tool presence and defect detection.
<div align="left">

## 6.4 Prototype 1 Development and Detection Results
<div align="left">

### 6.4.1 Prototype 1 Model Training
<div align="justify">
Prototype 1 was developed for Tool Presence Detection of the four main tools. The dataset images (Figure 24) were taken under varying image acquisition conditions listed in Table 6. 

<p align="center" id="fig24">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig22.png" width="80%">
  <br>
  <i>Figure 24. Prototype 1 Dataset Images</i>
  </p>
<div align="center">
  
*Table 6: Prototype 1 Dataset Imaging Acquisition Conditions*

<table id="tab6" width="100%" border="1" cellpadding="10" style="border-collapse: collapse; text-align: left;">
  <tbody>
    <tr>
      <td width="30%">Exposure</td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Low Exposure (Dim)</li>
          <li>Normal Exposure</li>
          <li>High Exposure (Bright)</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>Background</td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Trolley</li>
          <li>White cloth</li>
          <li>Blue cloth</li>
          <li>Bubble wrap</li>
          <li>Toolbox cover</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>Magnification</td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Normal</li>
          <li>Zoom in</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>Object placement</td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Toolbox within boundary</li>
          <li>Toolbox outside of boundary</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>Objects Present in Image</td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Toolbox with first layer tools (Non-defective)</li>
          <li>First layer non-defective tools without toolbox</li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>

<div align="justify">

After collecting all the images, they were manually labelled to classify the four tools under four distinct classes (Figure 25). 

* Class 1: Chop Phaco
* Class 2: Forceps Macpherson
* Class 3: Forceps Utrata
* Class 4: Hook Sinsky

<p align="center" id="fig25">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig23.png" width="80%">
  <br>
  <i>Figure 25: Prototype 1 Annotated Training Image with respective Tool Classes Via Roboflow</i>
  </p>
   
<div align=justify">
   
After labelling and dataset split are completed, the datasets ran through YOLOv8 to create the customized models. Prototype 1 underwent three iterations, with different dataset size, split ratios and training epoch size (Table 7).
<div align="center">

*Table 7: Prototype 1 Iterations Dataset Training Configuration*

<table id="tab7" width="100%" border="1" cellpadding="10" style="border-collapse: collapse; text-align: left;">
  <thead>
    <tr style="background-color: #f2f2f2;">
      <th>Iteration</th>
      <th>Dataset Size</th>
      <th>Dataset Split</th>
      <th>Training Epoch Size</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Iteration 1</td>
      <td>248</td>
      <td>87:13</td>
      <td>2</td>
    </tr>
    <tr>
      <td>Iteration 2</td>
      <td>248</td>
      <td>87:13</td>
      <td>25</td>
    </tr>
    <tr>
      <td>Iteration 3</td>
      <td>701</td>
      <td>75:25</td>
      <td>1</td>
    </tr>
  </tbody>
</table>
<div align="left">

### 6.4.2 Prototype 1 Detection Performance Analysis
<div align="justify">

To evaluate object detection function, detection results were analysed. The results have a visual output displaying the bounding boxes and the corresponding class name of the detected object. The legend for the visual output is as follows:

**Tool Presence Detection**
* Dark Blue: Chop Phaco
* Light Blue: Forceps Macpherson
* White: Forceps Utrata
* Green: Hook Sinsky
  
The models from all three iterations displayed unsatisfactory Tool Presence Detection (Figure 26). The models struggled with learning the tool features and perceived every aspect of the images as the four tools thus creating multiple bounding boxes images (Figure 26). Figure 27 also shows that the model did not learn to identify the four tools.

A large dataset is ideal for training as it increases the accuracy of detection. Moreover, producing better outcomes as the generalisation capabilities improve (Uddin & Lu, 2024). However, despite having a dataset of 701 for iteration 3, there was no ideal detection output. The results could suggest that having a large dataset is not the main contributor for a functioning detection model. Other variables such as training epoch size and imaging acquisition techniques used may be the cause of the poor performance instead.

<p align="center" id="fig26">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig24.png" width="80%">
  <br>
  <i>Figure 26. Detection result of (a) Prototype 1’s first iteration trained with epoch size of 2 (left), (b) Prototype 1’s second iteration trained with epoch size of 25 (middle), (c) Prototype 1’s third iteration trained with epoch size 1 (right)</i>
  </p>

<p align="center" id="fig27">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig25.png" width="80%">
  <br>
  <i>Figure 27. Normalised Confusion Matrix (Prototype 1 Model)</i>
  </p>
<div align="left">

## 6.5 Prototype 2 Development and Detection Results
<div align="justify">

Prototype 1 concluded with inconclusive results, making it unclear if the object detection model was functioning as intended. Hence, Prototype 2 was developed with improvements targeted at issues identified from Prototype 1, to troubleshoot and test the functionality and feasibility of the object detection model. The dataset size, imaging acquisition conditions and epoch size differ from Prototype 1.
<div align="left">

### 6.5.1 Prototype 2 Training
<div align="justify">

The main objective of Prototype 2 was to detect the presence of CP. The dataset was relatively small as it consists of images of CP only (Figure 28). There were two versions of Prototype 2, with Version 1 built with similar imaging conditions as Prototype 1 and Version 2 built with modifications to the dataset size, imaging acquisition technique and epoch size (Table 8).

<p align="center" id="fig28">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig26.png" width="80%">
  <br>
  <i>Figure 28. Image of CP (From Prototype 2 Dataset)</i>
  </p>
<div align="center">

*Table 8: Prototype 2 Version 1 And 2 Dataset Imaging Acquisition Conditions*

<table id="tab8" width="100%" border="1" cellpadding="10" style="border-collapse: collapse; text-align: left;">
  <thead>
    <tr style="background-color: #f2f2f2;">
      <th></th>
      <th>Version 1</th>
      <th>Version 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="30%"><b>Exposure</b></td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Low Exposure (Dim)</li>
          <li>Normal Exposure</li>
        </ul>
      </td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Normal Exposure</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td><b>Background</b></td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Trolley</li>
          <li>White cloth</li>
          <li>Toolbox cover</li>
        </ul>
      </td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Trolley</li>
          <li>White cloth</li>
          <li>Blue cloth</li>
          <li>Toolbox cover</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td><b>Magnification</b></td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Normal</li>
          <li>Zoom in</li>
        </ul>
      </td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Zoom in</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td><b>Object Placement</b></td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Anywhere as long as visible</li>
        </ul>
      </td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Anywhere as long as visible</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td>Objects Present in Image</td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Chop Phaco</li>
        </ul>
      </td>
      <td>
        <ul style="margin: 0; padding-left: 20px;">
          <li>Chop Phaco</li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>
<div align="justify">

After image collection, labelling was conducted to label CP as Chop Phaco (Figure 29). Version 1 has two iterations using the same dataset but trained at different epoch size and Version 2 has one iteration (Table 9). More iterations can be found in [Appendix G](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-g-object-detection-prototype-iteration-results). And once the dataset was splitted, the respective Version datasets was trained to create a customized YOLOv8 model. 

<p align="center" id="fig29">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig%2027.png" width="80%">
  <br>
  <i>Figure 29. Image of Labelled CP via Roboflow</i>
  </p>

<p align="center" id="tab9">
  <i>Table 9. Comparison Of Prototype 2 Version 1 And 2 Dataset Size, Dataset Split And Epoch Size</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab9.png" width="80%">
</p>
<div align="left">

### 6.5.2 Prototype 2 Detection Performance Analysis
<div align="justify">

The evaluation of detection results for Prototype 2 is indicated by a dark blue bounding box labeled with the class name, Chop Phaco, which appears upon successful detection. 

Prototype 2 Version 1’s confusion matrix reveals that the model failed to learn to detect CP as a tool and detects it as background instead (Figure 30). The detection results shows the model detects the background as CP (Figure 31).

<p align="center" id="fig30">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig%2028.png" width="80%">
  <br>
  <i>Figure 30. Normalised Confusion Matrix (Prototype 2 Version 1 Model)</i>
  </p>
  
<p align="center" id="fig31">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig%2029.png" width="80%">
  <br>
  <i>Figure 31. Detection Result Of Prototype 2 Version 1 Trained With Epoch Size Of 30 (Left), And Epoch Size 60 (Right)</i>
  </p>
<div align="justify">

Version 2 confusion matrix (Figure 32)  shows the model achieved a 0.39 confidence level for accurate tool detection.  Detection results indicate that the model successfully learnt the features of CP (Figure 33), and was able to detect either the entire tool or just the body of the tool. The model identified CP with a confidence level ranging from 0.12 to 0.46.

<p align="center" id="fig32">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig30.png" width="80%">
  <br>
  <i>Figure 32: Normalised Confusion Matrix For Prototype 2 Version 2 Model</i>
  </p>

<p align="center" id="fig33">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig31.png" width="80%">
  <br>
  <i>Figure 33. Detection Result Of Prototype 2 Version 2 Model (Epoch Size 100)</i>
  </p>
<div align="justify">

The  successful iterations of Prototype 2 showed that a small dataset size of ~150 was sufficient for object detection. Moreover, magnification should be consistent throughout the dataset. And an epoch size of more than 100 enables effective model learning.  Identification of these optimal model training conditions propelled  the project in  producing  tool presence detection and defect detection models.
<div align="left">

## 6.6 *MEDetect* Object Detection System 
<div align="justify">

The *MEDetect* object detection system was developed following the performance evaluations of the initial two prototypes. Several key factors guided this development phase. Firstly, the models were intentionally small, providing sufficient ability for model training while remaining accessible if troubleshoots were needed during the early stages of the project. Secondly, the dataset has consistent magnification. And lastly, the models were trained using epoch sizes exceeding 100. 

*MEDetect*’s implemented system consists of five individual models integrated to create the final system for tool presence detection and defect detection.

<div align="left">

### 6.6.1 *MEDetect* Model Training
<div align="justify">

Model 1 was trained to detect the presence of the four main tools (CP, FM, FU and HS) in the toolbox (Table 10). Models 2 to 5 were trained for individual tool defect identification (Table 10). Five individual models were used as magnification required for detection of tools’ presence and defect identification differs greatly and consistent magnification is required within each dataset.

<p align="center" id="tab10">
  <i>Table 10. Summary Of The 5 Models Used In The Final System</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab%2010_1.png" width="80%">
</p>
<div align="justify">

**Tool Presence Detection Model (Model 1)**

From Table 11, the dataset images (Figure 34) for Model 1 were taken using a magnification of 1.3 under natural lighting with exposure levels potentially fluctuating throughout the day but were readjusted using the Keyences software. 

<p align="center" id="tab11">
  <i>Table 11: Imaging Acquisition Conditions For Model 1</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab11.png" width="80%">
</p>

<p align="center" id="fig34">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig32.png" width="80%">
  <br>
  <i>Figure 34: Images Examples From Varying Scenarios Used For Training Model 1 For Tool Presence Detection</i>
  </p>
<div align="justify">

After images are collected, the images were annotated using Roboflow and the four tools were classified under four distinct classes (Figure 35). 

* Class 1: Chop Phaco
* Class 2: Forceps Macpherson
* Class 3: Forceps Utrata
* Class 4: Hook Sinsky

The dataset was then split into a 75:25 ratio. The model was then trained using YOLOv8 with an epoch size of 300 (Table 10).

<p align="center" id="fig35">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig33.png" width="80%">
  <br>
  <i>Figure 35. Labelling of 4 Main Tools In The Toolbox For Model 1 Via Roboflow</i>
  </p>
<div align="justify">
   
**Defect Identification Models (Model 2 to 5)**

The dataset images (Figure 36) for all models were taken at a magnification of 5.18. Images were captured under various conditions (Table 12), to prevent the model from overfitting.

<p align="center" id="fig36">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig34.png" width="80%">
  <br>
  <i>Figure 36. Model 2 Through 5 Dataset Images; CP (Top Left), FM (Top Right), FU(Bottom Left), HS (Bottom Right)</i>
  </p>
  
<p align="center" id="tab12">
  <i>Table 12: Model 2 to 5 Imaging Acquisition Conditions</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table12_1.png" width="80%">
</p>
<div align="justify">

After images were collected, the images were annotated (Table 13) using Roboflow with each model having two distinct classes labelled as follows: 

* Class 1: Defective_[Tool name]
* Class 2: Non-Defective_[Tool name]

The dataset was then split into a 75:25 ratio. The model was trained using YOLOv8 with an epoch size of 300 (Table 10).

<p align="center" id="tab13">
  <i>Table 13. Annotated Images Of Defective And Non-Defective Tools</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab13_1.png" width="80%">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab13_2.png" width="80%">
</p>

After all five models were trained, they were integrated using Python to create an automated inspection system ([Appendix F](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-f-integrated-object-detection-code)). In the first stage, a toolbox image will run through Model 1 for tool presence detection. Once inspection is completed, the system triggers an image cropping function to crop images of the individual identified tools. Once completed it will proceed to the second stage, defect detection. 

Each respective tool image would run through their respective model for defect inspection. Afterwards, inspection is completed. The completed flow of the programmed system is shown in Figure 37.

If any tool was not detected by Model 1, it would not trigger tool cropping and defect identification function.

**Note:** The results of defect detection are highly dependent on bounding boxes output by Model 1 as the cropped tool images are based on bounding boxes coordinates. It is possible that a portion of the tool tip could be cropped out leading to inaccurate results in defect inspection, however, more experimentation and validation is required in the future. 

<p align="center" id="fig37">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig%2035.png" width="80%">
  <br>
  <i>Figure 37. Process Of Integrated Object Detection System Through The Five Models</i>
  </p>
<div align="left">

### 6.6.2 *MEDetect* Model Detection Performance Analysis
<div align="justify">
   
The detection results would display the bounding boxes and the corresponding class name of the detected object. The legend for the visual output follows:

**Tool Presence Detection (Model 1)**
* Dark blue: Chop Phaco
* Light blue: Forceps Macpherson
* White: Forceps Utrata
* Green: Hook Sinskey

**Defect Detection (Model 2 - 5)**
* Dark blue: Defective
* Light blue: Non-defective

A total of five tests were conducted to evaluate the performance of the integrated automated inspection system (Table 14). The analysis of the confusion matrix and other forms of performance evaluation are presented in [Appendix D](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-d-performance-of-object-detection-models).

<p align="center" id="tab14">
  <i>Table 14. Summary Of Test Scenarios conducted on MEDetect's models</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab14.png" width="80%">
</p>
<div align="justify">

From the results of Test 1, Model 1 was able to accurately detect all four tools (Figure 38). And the defect detection models accurately identified all tools as non-defective (Table 15).

<p align="center" id="fig38">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig%2036.png" width="80%">
  <br>
  <i>Figure 38. Test 1 Tool Presence Detection Result</i>
  </p>
<div align="left">

<p align="center" id="tab15">
  <i>Table 15. Test 1 Defect Identification Results</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab15.png" width="80%">
</p>
<div align="justify">
   
From Test 2,  Model 1 could only detect the presence of CP, FU and FM (Figure 39). There was no output from Model 5 as it was not triggered as the presence of HS was not detected by Model 1. The other defect detection models succeeded in identifying CP, FM and FU as non-defective. However, the model also highlighted the other end of FU and labelled it as defective, producing a false negative result (Table 16).
   
<p align="center" id="fig39">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig37.png" width="80%">
  <br>
  <i>Figure 39. Test 2 Tool Presence Detection Result</i>
  </p>
<div align="left">

<p align="center" id="tab16">
  <i>Table 16. Test 2 Defect Detection Results</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab16.png" width="80%">
</p>
<div align="justify">

The results of Test 3 shows that Model 1 could detect the tool presence of all four trained tools (Figure 40). And Model 2 to 5 correctly identified all the tools as non-defective (Table 17).

<p align="center" id="fig40">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig38_new.png" width="80%">
  <br>
  <i>Figure 40: Test 3 Tool Presence Detection Result</i>
  </p>
<div align="left">
   
<p align="center" id="tab17">
  <i>Table 17. Test 3 Defect Detection Results</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab17.png" width="80%">
</p>
<div align="justify"> 
   
Results of Test 4 shows, Model 1 could only detect FM, FU and HS (Figure 41). However, Model 3 to 5 failed to correctly identify all three tool tips as defective (Table 18). 

In this test, FM was only defective on one arm and it was in the camera’s view, the defect became less apparent as the two arms overlapped. Thus, leading to incorrect results as the model perceived it as non-defective. FU defective tip was visible in the cropped image, but the model still incorrectly classified it as non-defective. While for HS, the defect was very subtle, a slight curvature near the tip, and the low resolution cropped image could have prevented the model to accurately distinguish the tip as defective. As shown in Table 18, the model identified the HS tip as defective and non-defective.

<p align="center" id="fig41">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig39.png" width="80%">
  <br>
  <i>Figure 41. Test 4 Tool Presence Detection Result</i>
  </p>
<div align="left">
   
<p align="center" id="tab18">
  <i>Table 18. Test 4 Defect Detection Results</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab18.png" width="80%">
</p>
<div align="justify"> 

Test 5 shows that Model 1 could only detect FM, FU and HS (Figure 42). Model 3 produced two bounding boxes at the tip of FM as it accurately identified the tip as defective while Model 4 and 5, did not produce satisfactory results for defect detection (Table 19). Model 4 identified FU as non-defective when the defect is visible in the image. And lastly, Model 5 could not detect whether HS is defective or non-defective.  

<p align="center" id="fig42">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig40.png" width="80%">
  <br>
  <i>Figure 42. Test 5 Tool Presence Detection Result</i>
  </p>
<div align="left">
   
<p align="center" id="tab19">
  <i>Table 19: Test 5 Defect Detection Results</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/tab19.png" width="80%">
</p>
<div align="justify"> 

Based on the evaluation of the five tests, there were several challenges observed. Firstly, when Model 1 is exposed to defective tools, it showed a weaker performance as it struggled to detect the presence of all tools, occasionally failing to detect CP and HS. 

Secondly, the defect detection models were unable to accurately classify defective tool tips. Defect detection for forceps was more challenging as defects such as differing arm lengths were used, making it harder for the model to differentiate resulting in inaccurate results in Test 4.  Forceps with different arm lengths are particularly hard to inspect as the defective arms could potentially be blocked from the camera’s view or overlapped. 

In summary, the models from *MEDetect*’s integrated system were trained with  relatively small datasets. Although the model has proven its ability to detect and inspect,  the accuracy of both could be improved. Future works for project improvement are addressed  in Section 9.
<div align="center">

# 7. Performance Testing
<div align="left">

## 7.1 Objective of Performance Testing 
<div align="justify">

The primary objective of the experiments is to rigorously evaluate the vision inspection learning model under conditions that simulate the post-operative surgical environment. Unlike controlled training, post-procedural tool inspection involves high variability in tool placement and conditions.

These experiments aim to quantify the model's reliability in ensuring surgical tool integrity and identifying compromised instruments through the technical objectives.
<div align="left">

## 7.2 WET DRY Cases
<div align="justify">

This test aims to assess the model's detection accuracy and defect identification across varying moisture levels. Because the project targets post-operative tool processing, the ability to detect wet instruments is essential, as it simulates the real-world condition of tools immediately following surgical use. The test dataset comprises 150 images, evenly divided between defective and non-defective sets (75 images each). The evaluation focused on four specific instruments: HS, CP, FM and FU. To replicate clinical conditions, tools were used in a wet state during the user try-out session. Validation images were reviewed by SNEC nursing staff to confirm they accurately reflected real clinical scenarios.

To simulate various clinical scenarios, we captured images using different wet-to-dry ratios:

* 1 Wet : 3 Dry
* 2 Wet : 2 Dry
* 3 Wet : 1 Dry
* All Wet Tools
  
**Note**: ‘All dry' scenario was excluded from this test to prioritize edge-case evaluation. Since dry-state performance was established during baseline training, this experiment was designed to focus on wet surgical tools as critical edge cases. This allows for a more stringent evaluation of the model’s proficiency in detecting tools and classifying trained defects beyond standard dry-state condition.

The model’s performance drops in "wet" scenarios, a trend that is likely a direct consequence of the training dataset consisting exclusively of "dry" tools. Detection of non-defective tools remains high across all scenarios, averaging 91% to 100% for most tool types, though the 2 Wet/2 Dry scenario showed a significant dip to 74.2% (Table 20). HS and FM tools achieved tools presence detection of >90% regardless of the wet/dry ratio, while CP and FU were notably less reliable, particularly in high-moisture scenarios (3 to 4 wet tools). For non-defective tools, HS had the lowest defect identification accuracy of 30.7% (Table 21), frequently misidentifying non-defective tools as defective. Conversely, for actual defective tools, HS tool presence detection accuracy maintained at 100% despite increasing wetness, with defect detection peaking at 100% in the 4 Wet scenario (Table 22). FM and CP tools showed strong accuracy (~90%) in identifying non-defective states but failed significantly in identifying actual defects, with FM dropping to 2.1% accuracy for defective tool identification (Table 23).

<p align="center" id="tab20">
  <i>Table 20. Wet/Dry: Tool Presence Detection Accuracy (%)</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2017.png" width="80%">
</p>

<p align="center" id="tab21">
  <i>Table 21. Wet/Dry: Tool Defect Identification Accuracy (%)</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2018.png" width="80%">
</p>

<p align="center" id="tab22">
  <i>Table 22. Wet/Dry: Tool Presence Detection Accuracy (%)</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/Table%2019.png" width="80%">
</p>

<p align="center" id="tab23">
  <i>Table 23. Wet/Dry: Tool Defect Identification Accuracy (%)</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/Table%2020.png" width="80%">
</p>

<p align="center" id="fig43" >
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2042.png" width="80%">
  <br>
  <i>Figure 43. Overall Model Performance: Presence Detection vs Defect Identification</i>
  </p>
<div align="justify">

Overall, the model’s performance in wet cases remains acceptable for basic presence detection, yet it faces a significant diagnostic hurdle with an 83.1% tool presence detection rate compared to only 49.5% for defect identification (Figure 43). As the model was trained exclusively on dry tools, it consistently performs better in dry conditions where visual features remain clear and undistorted. These results suggest that while the model is performing reasonably acceptably fundamentally, it would benefit greatly from an expanded training dataset that includes a wider variety of wet scenarios and fluid-obscured defects to improve its reliability in real-world applications.
<div align="left">

## 7.3 Optical Changes 
<div align="left">

## 7.3.1 Exposure Changes
<div align="justify">

We evaluated the model under both underexposed and overexposed conditions to simulate extreme edge cases. The primary objective of this test is to verify the model's functional consistency across a spectrum of lighting environments. In a real-world clinical setting, external factors such as overhead fluorescent lighting or proximity to windows can cause significant shifts in ambient light. Standard illumination in clinical environments where surgical instrument inspection are conducted at typically operates within a range of 100–200 lux (Healthcare Communal and Circulation Areas, n.d.)

While the Keyence camera’s integrated “Auto Brightness” control effectively standardizes resolution and exposure levels regardless of the physical setup, this test serves as a critical edge-case validation (Figure 44).

<p align="center" id="fig44">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig%2043.png" width="80%">
  <br>
  <i>Figure 44. Brightness Auto Adjusted by KEYENCE Camera (Mean Brightness =123.3)</i>
  </p>

<p align="center" id="tab24">
  <i>Table 24. Underexposed Image vs Overexposed Image Used</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2021.png" width="80%">
</p>

<p align="center" id="tab25">
  <i>Table 25. Defect Identification Results	</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2022.png" width="80%">
</p>
<div align="justify">   
   
**Tool Presence Detection:** The auto-adjusted control image (Figure 44) achieved a 100% success rate in detecting all four trained tools (Table 24). In underexposed conditions, the model demonstrated high resilience, successfully identifying all tools with superior confidence scores compared to the control group. This suggests that the model’s feature extraction is highly effective in low-light scenarios. In Overexposed Conditions however, while detection for HS remained consistent with control levels, the model struggled with high-luminance environments (Table 24). Specifically, it failed to detect CP and exhibited "class confusion" between FM, and FU likely due to surface glare arising from the high exposure.

**Defect Identification:** CP and FM were highly reliable in defect identification in both control and underexposed states. However, performance degraded significantly under overexposed conditions, where the model failed to perform defect identification accurately entirely. This suggests that high exposure "washes out" the surface textures necessary for defect detection. Results for the HS and FU were categorized as inconclusive across all lighting scenarios (Table 25). This was not a failure of the model itself, but rather a limitation of the bounding box parameters, which failed to accurately and sufficiently encompass the tool tips.

<div align="left">   

### 7.3.2 Resolution Changes
<div align="justify">   

While the Keyence camera utilizes an "Auto Focus" feature to adjust image focus, this edge test is essential to verify the model's trained performance. By manually overriding the focus, we simulated potential blurring (Figure 46) to determine the impact on tool detection and defect identification. This validation defines the model's operational boundaries, ensuring that critical identification tasks remain accurate even when image quality decreases. Prior to testing, the model was not trained on blurred images of the toolbox. Only non-defective tools were used in this test. For the purposes of this test, a standard reference image was captured at a focal setting of 343, while an intentionally blurred counterpart was captured by intentionally reducing the focal value to 318.

<p align="center" id="fig45">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2044.png" width="80%">
  <br>
  <i> Figure 45. Image of Toolbox with Auto Adjusted Focus (Focus = 343)</i>
  </p>
  
<p align="center" id="fig46">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2045.png" width="80%">
  <br>
  <i>Figure 46. Blurred image of toolbox (Focus = 318)</i>
  </p>
  <div align="justify">   

The model successfully identified all four tools (Figure 45) despite lower resolution; however, the model failed to determine if any of the tools were defective or not.  
<div align="left">   

## 7.4 Orientation and Position Changes
<div align="left">   

### 7.4.1 Rotation Test
<div align="justify">   

The test aims to evaluate model accuracy in tool presence detection and defect identification under real-world conditions where tool orientation may vary during manual sorting. The evaluation utilized a test dataset of 50 images of only non-defective tools. The test was divided into two scenarios:

1. **1 Tool Rotation:**  20 Images
2. **2 out of 4 Tool Rotation:**  30 Images

**Note:** With a test database size of 50, the test focused on generating enough data points to prove a performance gap. The results showed a 65% drop in performance between seeing a tool and defect identification when rotated in the first 2 test scenarios. Therefore, testing further rotations would have yielded the same conclusion.

**Example of Rotations:** 
<p align="center">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/new.png" width="80%">
  </p>
  <div align="justify">   

<p align="center" id="tab26">
  <i>Table 26. Rotation: Tool Presence Detection Accuracy (%)</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/Table%2023.png" width="80%">
</p>

<p align="center" id="tab27">
  <i>Table 27. Rotation: Tool Defect Identification Accuracy (%)</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/Table%2024.png" width="80%">
</p>

<p align="center" id="fig47">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2046.png" width="80%">
  <br>
  <i>Figure 47. Average Accuracy by Tool Type </i>
  </p>

<p align="center" id="fig48">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2047.png" width="80%">
  <br>
  <i>Figure 48. Accuracy by Scenario (Average of All Tools) </i>
  </p>
<p align="center" id="fig49">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2048.png" width="80%">
  <br>
  <i>Figure 49. Overall Model Performance Comparison </i>
  </p>
  <div align="justify">   
     
As the number of rotated tools increases, the model's ability to detect tool presence declines (Table 26). Presence detection dropped from an average of 85.0% in the single-rotation scenario to 74.2% in the double-rotation scenario (Figure 48). This suggests that multiple irregular orientations create "visual noise" that confuses the model's logic, making it more difficult to confirm that a tool is present which is a critical failure since detection is a prerequisite for defect identification. 

Defect identification accuracy remains low across both scenarios, averaging 13.8% for single rotations and 15.8% for double rotations (Figure 48). While the overall average is relatively similar, individual tool performance fluctuated. HS remained the most accurate in defect identification, though its accuracy dipped from 40.0% to 33.3% (Table 27) as complexity rose. Conversely, CP saw a slight improvement from 15.0% to 23.3% (Table 27), suggesting that in some cases, the model may require more "examples" of irregularities in a single frame to trigger a defect classification.

This test proves that when tools are rotated, the model is reliable for detecting tool presence but unreliable in defect identification. 
<div align="left">   

### 7.4.2 Overlap Test
<div align="justify">   

The overlap tests evaluate model accuracy in tool presence detection and defect identification under real-world conditions where tools position may vary during manual sorting.
<div align="left">   

#### 7.4.2.1 Overlap with Trained Tools
<div align="justify">   

The evaluation utilized a test dataset of 90 images. Overlaps only happen among the 4 trained tools *(Figure 50)* . Only non-defective tools were used in this test. The test was divided into two scenarios:
- **1 Trained Tool Overlapping:**  60 Images
- **2 Trained Tools Overlapping:**  30 Images
  
**Example of Overlaps of Trained Tools:**

<p align="center" id="fig50">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure49.png" width="80%">
  <br>
  <i>Figure 50. Overlap Test Of Trained Tools (HS And CP) </i>
  </p>

<p align="center" id="tab28">
  <i>Table 28. Overlapping of  Trained Tools: Tool Presence Detection Accuracy (%) </i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2025.png" width="80%">
</p>

<p align="center" id="tab29">
  <i>Table 29. Overlapping of Trained Tools: Defect Identification Accuracy (%) </i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2026.png" width="80%">
</p>

<p align="center" id="fig51">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2050.png" width="80%">
  <br>
  <i>Figure 51. Average Accuracy by Tool Type (Overlap of Trained Tools) </i>
  </p>
<p align="left">

FM has the highest presence detection (86.7%) but absolute zero defect identification (Figure 51). This is because there were many instances where FU was identified incorrectly as FM. When such scenarios happen, the model will analyse FU’s tip instead of FM resulting in no results shown. 

Despite a low presence detection rate of 32.5% (Figure 51), HS achieves the highest defect identification accuracy at 15.0% (Table 29). This suggests that its small, distinct tip is easier for the model to isolate and analyze against the backdrop of a larger tool compared to the visual confusion caused by two large, similar instruments overlapping.

<p align="center" id="fig52">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2051.png" width="80%">
  <br>
  <i>Figure 52. Accuracy by Scenario (Overlap of Trained Tools) </i>
  </p>
<p align="justify">
   
In all cases, performance of tool presence detection and defect identification is inversely proportional to the number of overlaps (Figure 52). 

<p align="center" id="fig53">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2052.png" width="80%">
  <br>
  <i> Figure 53. Overall Performance: Overlap of Trained Tools </i>
  </p>
<p align="justify">

All in all, the model has proven itself to be a capable locator but an unreliable inspector when visual clutter is present (Figure 53). Its inability to distinguish between two similar tools when overlapping and its dependency on a perfectly clear view of the tool tip remain its primary bottlenecks.
<p align="left">

#### 7.4.2.2 Overlap with Untrained Tools 
<p align="justify">

The evaluation utilized a test dataset of 200 images. Trained tools were set to overlap with 4 other untrained tools (Speculum Liberman, Needle Holder Castroviejo, Forceps Moorfield Dissecting and Repositor Iris) *(Table 27)*. Only non-defective tools were used. The test was divided into two scenarios:

- **1 Overlap:**  80 Images
- **2 Overlaps:**  120 Images

**Example of Overlap:**

<p align="center" id="fig54">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2053.png" width="80%">
  <br>
  <i> Figure 54. Overlap of Untrained Tools (FM and Repositor Iris) </i>
  </p>
<p align="justify">

**Untrained Tools Involved In The Overlaps:**

<p align="center" id="tab30">
  <i>Table 30. Untrained Tools Used for Overlap Test</i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2027.png" width="80%">
</p>
<div align="justify">   

<p align="center" id="tab31">
  <i>Table 31. Overlap with Untrained Tools: Tool Presence Detection Accuracy (%) </i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2028.png" width="80%">
</p>

<p align="center" id="tab32">
  <i> Table 32. Overlap with Untrained Tools: Defect Identification Accuracy (%) </i>
   <br>
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/table%2029.png" width="80%">
</p>
<div align="justify">   

<p align="center" id="fig55">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2054.png" width="80%">
  <br>
  <i> Figure 55. Average Accuracy by Tool Type (Overlap with Untrained Tools) </i>
  </p>
<p align="justify">

<p align="center" id="fig56">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2055.png" width="80%">
  <br>
  <i>Figure 56. Accuracy by Scenario (Overlap with Untrained Tools)</i>
  </p>
<p align="justify">
   
In scenarios where one trained tool overlaps with an untrained tool, the model maintains a moderate level of detection capability but struggles almost entirely with defect identification.

**Tool Presence Detection:** When there is 1 overlap, the model achieves an accuracy of 65.3%. This is actually notably higher than the "2 Overlap" scenario (50.6%) (Figure 56), suggesting that increased visual clutter further degrades the model's spatial reasoning.

**Defect Identification:** Performance in this category is critically low at 1.9%  (Figure 56) for a single overlap indicating that the model is almost completely unable to analyze the integrity of the tool when its silhouette is partially obscured by an unfamiliar tool.

<p align="center" id="fig57">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/figure%2056.png" width="80%">
  <br>
  <i>Figure 57. Overall Performance: Overlap with Untrained Tools</i>
  </p>
<p align="justify">
   
The model is partially effective at presence detection (averaging 58.0% overall across all overlap scenarios) but functionally ineffective at defect identification (averaging 2.6% overall) (Figure 57).

The drop-off from 65.3% (1 Overlap) to 50.6% (2 Overlap) (Figure 56) for presence detection suggests that the model’s performance is inversely proportional to the complexity of the overlap. The marginal increase in defect identification during complex overlaps is likely due to the tool tips remaining visible by chance, rather than a genuine improvement in the model's performance.
<div align="center">   

# 8. Survey Results and Summary

<div align="justify">
   
While the validation of the computer vision detection pipeline demonstrates the technical capability of the automated instrument identification, system adoption in clinical environments ultimately depends on the system’s usability, interpretability and user trust. Therefore, it is necessary to evaluate *MEDetect* not only as a detection model but also as an integrated clinical support tool.

A usability survey was therefore conducted with, in total, 18 inspection staff and stakeholders from SNEC who reviewed the system through either a live demonstration or a video walkthrough of the inspection workflow.

This evaluation was designed to assess the system’s usability, user acceptance, and alignment with existing inspection workflows to validate the practical application of *MEDetect* in a clinical setting.

## 8.1 Perceived Usefulness
Responses indicated that the system was generally perceived as beneficial to the inspection workflow. The majority of respondents rated the system as somewhat helpful (13 responses) or very helpful (4 responses) in their work. Only a small minority indicated that the system would be unhelpful. These results suggest that automated detection and classification features are viewed as a valuable support tool for surgical instrument inspection.

## 8.2 Trust in Automated Classification
Survey responses revealed that while users are open to AI-assisted detection, they still prefer to maintain human verification in the inspection process. Most respondents indicated that they would trust the system but still require in-person verification (11 responses). A smaller number reported only slight trust (5 responses), while a minority indicated full trust in the system’s classification results.

This outcome highlights the importance of designing the system as a decision-support tool rather than a fully autonomous inspection system, reinforcing the need for human oversight during critical verification tasks.

## 8.3 Acceptance of AI-Assisted Inspection
Participants generally expressed positive attitudes toward the use of AI in assisting inspection workflows. Most respondents reported that they felt comfortable with AI assisting inspections (16 responses), with one respondent indicating they were very comfortable. Only a small minority expressed discomfort with AI-assisted inspection.

These findings suggest that the integration of computer vision into inspection workflows is acceptable to users when implemented as a supportive tool.

## 8.4 Ease of Learning and Operating the System
Usability feedback for the *MEDetect* interface was highly positive. The vast majority of respondents indicated that the system was easy to learn and operate (17 responses), while one respondent rated the system as very easy to use. No respondents reported that the system was difficult to use.

This result supports the effectiveness of the interface design in presenting inspection results clearly and guiding users through the inspection workflow.

## 8.5 Importance of Manual Override
Participants also emphasized the importance of maintaining the ability to override AI-generated classifications. Most respondents indicated that manual override functionality was important (11 responses) or very important (5 responses). Only a small number of respondents considered this feature to be less important.

This finding reinforces the design decision to incorporate a manual override mechanism with multi-user verification, ensuring that inspection staff can intervene when automated classification results require further confirmation.

## 8.6 Willingness to Adopt the System
When asked whether they would be willing to use the system in their workflow, all respondents indicated that they would be willing to adopt the system. This result suggests strong overall acceptance of the *MEDetect* system as a tool to assist with surgical instrument inspection.

Overall, the survey results ([Appendix E](https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Appendix.md#appendix-e-medetect-usability-survey)) indicate that the *MEDetect* system was well received by inspection staff and stakeholders. Participants found the interface easy to learn and operate, expressed comfort with AI-assisted inspection, and recognized the potential usefulness of automated tool detection within their workflow. At the same time, respondents emphasized the continued importance of human verification and manual override capabilities, highlighting the need for AI systems in clinical environments to function as decision-support tools rather than fully automated replacements.

These findings validate the design approach adopted in *MEDetect*, which combines automated detection with human oversight to support safe and reliable surgical instrument inspection.


<div align="center">
   
# 9. Future Work

<p align="center" id="fig58">
  <img src="https://github.com/ohhtiaf/EIM-401_Automated-Inspection-of-Surgical-Tools/blob/main/Report%20Images/fig56.png" width="80%">
  <br>
  <i>Figure 58. 3 Step Engineering Roadmap</i>
  </p>
<div align="justify">

The current iteration of the system provides a robust proof of concept; however, transitioning from a prototype to a clinical tool requires systematic optimization. While the project’s findings demonstrate significant potential for success, further development should target to achieve a minimum of 95% statistical confidence interval in both Tool Presence Detecction and Defect Identification. The 95% confidence level is the clinical standard because it aligns with the $p < 0.05$ threshold required to prove that results are not due to random chance (Lucht, 2025). This benchmark provides a universally accepted rigorous framework for balancing the risks of over-diagnosis against the safety of missing a critical defect. 

To reach this benchmark and ensure the system's reliability, the following multi-phased engineering roadmap can be established.
<div align="left">

**Dataset Expansion and Generalization** 
<div align="justify">
   
To move beyond the initial subset of four specialized tools, the database should be scaled to encompass the full surgical inventory.
* **Target Volume:** The dataset of trained images should be increased to a minimum of 10,000+ annotated images to improve tool presence detection across a wider variety of tray configurations. A baseline of 10,000 training images is recommended to facilitate a high-confidence test set, satisfying FDA requirements for demonstrating clinical safety and performance (Research, 2021).
  
* **Incorporate Edge Cases in Training Dataset:** Training should include high-variance edge cases, to ensure the model maintains high sensitivity across all operational environments. Key factors include:
   * **Realistic Clinical Lighting:** Training images should reflect the diverse illumination levels found in medical facilities, ranging from standard exam room lighting to high-intensity procedural areas (typically 500–1,500+ lux  (Lighting Solutions for Hospitals and Healthcare Facilities, 2024)).
   * **Post-Procedural Tool Conditions:** Training images should be obtained from authentic, post-procedural tools to accurately capture realistic states of wetness, dryness, and biological residue. To ensure clinical validity, these images should be vetted by inspection nurses to verify they depict the precise conditions encountered during in real-world scenarios. 
<div align="left">
   
**High-Sensitivity Defect Identification**
<div align="justify">
   
Future development should shift from general classification models to specialized architectures optimized for granular integrity defects.

* **Architectural Scaling:** Utilise stronger models specifically designed for fine defect inspection (such as SurgScan (Ain et al., 2025)) to expand the system’s inspection and detection capability.
* **Granular Defect Identification:** Current detection is limited to macro-level breakage or missing tool tips. Next phase of project should focus on identifying fine-scale structural deformities, including:
    * Curvature Deviations: Identifying subtle tip misalignments.
    * Partial Fractures: Detecting microscopic cracks before they lead to tool failure during surgery.
<div align="left">

**Unified Inference Pipeline**
<div align="justify">
   
The current sequential workflow faces a significant limitation in error propagation, where the detection of a tool is a strict prerequisite for any subsequent defect analysis. If the initial model fails to localize an instrument due to overlapping tools, glare, or complex shadows, the system effectively ignores that tool's structural integrity. This creates a critical "blind spot" in the inspection process, as tool defects remain unanalyzed if the primary localization fails.

To resolve this, future development should consider transitioning to a unified, single-stage inference pipeline using advanced architectures like DETR (Detection Transformer) and Mask R-CNN. Unlike traditional models that look at localized pixels, DETR analyzes the entire image context at once, allowing it to accurately identify tool presence even when instruments are partially obscured or clustered on a surgical tray (Kamboj, 2024).  Meanwhile, Mask R-CNN (Vina, 2025) solves the challenge of granular defect detection by moving beyond simple bounding boxes to pixel-level instance segmentation. It generates a precise digital mask of each tool allowing the model to isolate the instrument’s specific geometry to inspect for sub-millimeter structural irregularities.

From a system-level perspective, transitioning to a multi-task learning architecture will significantly optimize computational efficiency by reducing the cumulative VRAM footprint, thereby facilitating deployment in clinical settings. Furthermore, a consolidated model mitigates the inherent risk of error propagation found in the current sequential workflow, where defect analysis is strictly contingent upon successful preliminary localization. By executing both tasks in a single forward pass, the system will eliminate the possibility of overlooked defects due to detection failures and drastically reduce inference latency, ensuring a more resilient and responsive real-time inspection environment. 
<div align="left">
   
**Conclusion**
<div align="justify">
   
Once a more representative dataset has been established, subsequent work should focus on refining the detection framework itself which may involve a deeper evaluation of neural network architectures or higher-resolution pipelines better suited to identifying tool structural irregularities and fine integrity defects. 

To improve confidence in the model’s performance, future validation should also be conducted using larger and more representative test sets. Rather than relying on point estimates of accuracy, subsequent evaluations should report confidence intervals derived from sufficiently large validation samples with the goal of achieving performance levels that are statistically stable and clinically interpretable. This would provide a clearer indication of the system’s suitability for real-world deployment.

While the current results were less than ideal for immediate clinical adoption, they show a clear direction for continued development. By improving dataset quality, refining the model architecture and validating performance on broader clinical scenarios, *MEDetect* can progress from being an early proof of concept towards a more accurate and clinically reliable inspection tool.

Beyond the technical outcomes, this project provided valuable insight into the challenges of developing an end-to-end system that integrates machine learning, user interface design and hardware components. Through the development of the detection pipeline, we gained a deeper understanding of computer vision workflows, particularly in how training parameters such as epoch size influence model performance.

The integration of industrial imaging hardware also exposed the gap between controlled experimental setups and real-world deployment. Working with the Keyence camera required adapting to proprietary communication protocols and limitations that differ significantly from standard industrial configurations which led us to develop alternative solutions like API-based communication and FTP-based image transfer with the goal of bridging the gap between hardward and software component interactions within a proof-of-concept environment.

More broadly, the project required exploration beyond what was taught in class. Areas such as system integration and network communication are just two that we would not typically encounter but became essential in developing a functional inspection system.

Overall, this experience highlighted the importance of adaptability and system thinking in engineering design centered around users. It demonstrated that developing a practical solution extends beyong individual components, requiring the seamless integration of multiple technologies into a cohesive and reliable platform. *MEDetect* therefore represents not only a technical proof of concept, but also our learning process in translating theoretical knowledge into a system capable of supporting real-world clinical workflows.

---
<div align="center">

# References
<div align="left">

* Gard, S. (2025, August 25). *AI-driven Quality Control in Manufacturing: Boost Product Quality and Cut Costs*. [https://www.quytech.com/blog/ai-driven-quality-control-in-manufacturing/](https://www.quytech.com/blog/ai-driven-quality-control-in-manufacturing/)
* Iowa State University. (n.d.). *Visual Acuity of the Human Eye*. [https://www.nde-ed.org/NDETechniques/PenetrantTest/Introduction/improvingdetection.xhtml](https://www.nde-ed.org/NDETechniques/PenetrantTest/Introduction/improvingdetection.xhtml)
* Deepak Care. (2025, September 25). *Maintaining Precision: Best Practices for Care and Handling of Ophthalmic Surgical Instruments*. [https://deepakcare.com/maintaining-precision-best-practices-for-care-and-handling-of-ophthalmic-surgical-instruments/](https://deepakcare.com/maintaining-precision-best-practices-for-care-and-handling-of-ophthalmic-surgical-instruments/)
* Steelco S.p.A. (2024, February 27). *SUIS - Surgical Instrument Vision System - Steelco*. Steelco. [https://www.steelcogroup.com/technology/surgical-instrument-scanner/](https://www.steelcogroup.com/technology/surgical-instrument-scanner/)
* Keyence.(n.d.). *Zoom smart camera, Standard range, Colour, 1.6M pixel - VS-L160CX | KEYENCE Singapore*. [https://www.keyence.com.sg/products/vision/vision-sys/vs/models/vs-l160cx/](https://www.keyence.com.sg/products/vision/vision-sys/vs/models/vs-l160cx/)
* Keyence (n.d.). *Vision System with Built-in AI*. [https://www.keyence.com.sg/products/vision/vision-sys/vs/](https://www.keyence.com.sg/products/vision/vision-sys/vs/)
* International Organization for Standardization. (2019). *Ergonomics of human-system interaction — Part 210: Human-centred design for interactive systems (ISO Standard No. 9241-210:2019)*. [https://cdn.standards.iteh.ai/samples/77520/8cac787a9e1549e1a7ffa0171dfa33e0/ISO-9241-210-2019.pdf](https://cdn.standards.iteh.ai/samples/77520/8cac787a9e1549e1a7ffa0171dfa33e0/ISO-9241-210-2019.pdf)
* Nielsen, J. (1994, April 24). *10 usability heuristics for user interface design. Nielsen Norman Group.* [https://www.nngroup.com/articles/ten-usability-heuristics/](https://www.nngroup.com/articles/ten-usability-heuristics/)
* Yablonski, J. (n.d.). *Hick’s Law. Laws of UX.* [https://lawsofux.com/hicks-law/](https://lawsofux.com/hicks-law/)
* Ultralytics. (n.d). *Yolov11 vs Yolov8: A Comprehensive Technical Comparison of Real-Time Vision Models*. [https://docs.ultralytics.com/compare/yolo11-vs-yolov8/](https://docs.ultralytics.com/compare/yolo11-vs-yolov8/)
* Ultralytics. (2023). *Explore Ultralytics YOLOv8*. [https://docs.ultralytics.com/models/yolov8/](https://docs.ultralytics.com/models/yolov8/)
* He, L. H., Zhou, Y. Z., Liu, L., Cao, W. & Ma, J. H. (2025). *Research on objection detection and recognition in remote sensing images based on YOLOv11*. [https://www.nature.com/articles/s41598-025-96314-x](https://www.nature.com/articles/s41598-025-96314-x)
* Uddin, S. & Lu, H, H. (2024). *Dataset meta-level and statistical features affect machine learning performance*. [https://www.nature.com/articles/s41598-024-51825-x](https://www.nature.com/articles/s41598-024-51825-x)
* Sivakumar. M., Parthasarathy, S. and Padmapriya, T. (2024). *Trade-off between training and testing ratio in machine learning for medical image processing*. PeerJ. [https://doi.org/10.7717/peerj-cs.2245](https://doi.org/10.7717/peerj-cs.2245)
* Ain, Q. U., Ahmed, Shafqat, Z., & Butt, N. A. (2025). *Real-Time Surgical Instrument Defect Detection via Non-Destructive Testing*. ArXiv (Cornell University). [https://doi.org/10.48550/arxiv.2510.14525](https://doi.org/10.48550/arxiv.2510.14525)
* Lucht, R. (2025, January 24). *The 95% Confidence Interval’s Impact on Experimentation Results*. Geteppo.com; Eppo. [https://www.geteppo.com/blog/95-percent-confidence-intervals-impact-experimentation](https://www.geteppo.com/blog/95-percent-confidence-intervals-impact-experimentation)
* Research, C. for D. E. and. (2021, May 11). *E9(R1) Statistical Principles for Clinical Trials: Addendum: Estimands and Sensitivity Analysis in Clinical Trials*. U.S. Food and Drug Administration. [https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e9r1-statistical-principles-clinical-trials-addendum-estimands-and-sensitivity-analysis-clinical](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e9r1-statistical-principles-clinical-trials-addendum-estimands-and-sensitivity-analysis-clinical)
* Glamox. (2024). *Lighting solutions for hospitals and healthcare facilities*. Glamox Prod. [https://www.glamox.com/en/pbs/application-guide/healthcare/](https://www.glamox.com/en/pbs/application-guide/healthcare/)
* Kamboj, H. (2024, October 15). *DETR: Overview and Inference*. LearnOpenCV. [https://learnopencv.com/detr-overview-and-inference/](https://learnopencv.com/detr-overview-and-inference/)
* Vina, A. (2025). *Mask R-CNN Explained: Guide, Uses & YOLO | Ultralytics*. Ultralytics.com. [https://www.ultralytics.com/blog/what-is-mask-r-cnn-and-how-does-it-work](https://www.ultralytics.com/blog/what-is-mask-r-cnn-and-how-does-it-work)
* MiniTec. (n.d.). *T-Slotted aluminum extrusions and Rhombus Nuts*. [https://www.minitecframing.com/Products/Screw_And_Nuts/Catalog_Pages/Rhombus_Nuts/21.1354_Rhombus_Nut_F.html](https://www.minitecframing.com/Products/Screw_And_Nuts/Catalog_Pages/Rhombus_Nuts/21.1354_Rhombus_Nut_F.html)

---

#  J: Role Allocation

<div id="tab59">
<div align="center">

*Table 59. Role and Responsibilities*

<table width="100%" border="1" cellpadding="10" style="border-collapse: collapse; text-align: left;">
  <thead>
    <tr style="background-color: #f2f2f2;">
      <th>Role</th>
      <th>Responsibilities</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Hardware/Validation</td>
      <td>Celest</td>
    </tr>
    <tr>
      <td>UI/UX</td>
      <td>Matthias</td>
    </tr>
    <tr>
      <td>Object Detection Model Training and System Development</td>
      <td>Valerie</td>
    </tr>
    <tr>
      <td>User Specifications</td>
      <td>Faith</td>
    </tr>
  </tbody>
</table>
<div align="center">

<b>Report Writing Allocation</b>

<table style="width: 100%; border-collapse: collapse; border: 1px solid black; font-family: Arial, sans-serif;">
  <thead>
    <tr style="background-color: #d3d3d3; text-align: left;">
      <th style="border: 1px solid black; padding: 10px;">Name</th>
      <th style="border: 1px solid black; padding: 10px;">Sections</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border: 1px solid black; padding: 10px; font-weight: bold;">Celest Boh</td>
      <td style="border: 1px solid black; padding: 10px;">Section 7, 9, Appendix C and J</td>
    </tr>
    <tr>
      <td style="border: 1px solid black; padding: 10px; font-weight: bold;">Faith Ho</td>
      <td style="border: 1px solid black; padding: 10px;">Section 1, 2, 3, 4, Appendix A, E and I</td>
    </tr>
    <tr>
      <td style="border: 1px solid black; padding: 10px; font-weight: bold;">Matthias Khoo</td>
      <td style="border: 1px solid black; padding: 10px;">Section 5, 8 and Appendix H and Appendix E</td>
    </tr>
    <tr>
      <td style="border: 1px solid black; padding: 10px; font-weight: bold;">Valerie Koh</td>
      <td style="border: 1px solid black; padding: 10px;">Section 6, Appendix B,D,F and G</td>
    </tr>
  </tbody>
</table>


[Back to top](#list-of-tables)
