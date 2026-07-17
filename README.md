<div align="center">

# ?? App Review Insights Analyser

**Transforming chaotic user feedback into a clean, actionable weekly pulse.**

[![Live Prototype](https://img.shields.io/badge/Live_Prototype-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://app-review-insights-analyser-roan.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Llama-3](https://img.shields.io/badge/Llama_3.3_70b-0466C8?style=for-the-badge)](#)

</div>

<br>

> **Situation:** Product, Growth, and Support teams need to know exactly what users are complaining about to prioritize roadmaps effectively. Manually reading thousands of App Store & Play Store reviews is impossible.
> 
> **Task:** Build a fully automated intelligence pipeline to programmatically extract raw mobile app reviews and transform them into a clean, actionable one-page weekly pulse for leadership, entirely hands-free.

---

## ?? Dashboard Preview

<div align="center">
  <img src="Docs/App%20analyser%20agent%20screenshot%201.png" alt="Intelligence Pipeline Execution" width="800"/>
  <br><br>
  <img src="Docs/App%20analyser%20agent%20screenshot%202.png" alt="Weekly Pulse Metrics" width="800"/>
  <br><br>
  <img src="Docs/App%20analyser%20agent%20screenshot%203.png" alt="Pipeline Completion" width="800"/>
</div>

---

## ??? The AI Workflow
Our system executes a seamless, 4-step pipeline directly from the dashboard:

1. ?? **Data Ingestion:** Automatically scrapes the latest 8–12 weeks of reviews from both the iOS App Store and Google Play Store.
2. ?? **Categorization:** Processes the raw data and groups the feedback into a maximum of 5 critical themes.
3. ?? **Synthesis:** Uses Llama-3.3-70b to generate a highly scannable, one-page weekly note containing the top 3 themes, 3 real user quotes, and 3 immediate action ideas.
4. ?? **Distribution:** Automatically drafts an email containing the weekly note so leadership has a quick health pulse waiting in their inbox.

---

## ?? How to Re-Run for a New Week
1. Open the [UI Prototype](https://app-review-insights-analyser-roan.vercel.app/).
2. Navigate to the **Run Pipeline** (Rocket Icon) tab on the sidebar.
3. Click the **Run New Week** button to trigger the Python backend API (hosted on Render).
4. Watch the Intelligence Pipeline visualize the backend processing in real-time.
5. Check the **Weekly Note** and **Email Draft** tabs to see your newly generated insights!

---

## ?? Theme Legend
* ?? **UI/UX Issues**: Complaints about app freezing, blank screens, and navigation issues.
* ??? **Onboarding & KYC**: Friction during account creation, document verification delays.
* ?? **Payments & Transactions**: Issues with money transfers, failed payments, and pending statuses.
* ?? **Customer Support**: Lack of response from support, poor customer service experience.
* ? **Feature Requests**: Requests for new tools, dark mode, or better expense tracking.

<br>
<div align="center">
  <i>Built with ?? using Generative AI, Python, and Llama 3</i>
</div>
