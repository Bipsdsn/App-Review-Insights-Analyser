# App Review Insights Analyser ??

**Live Prototype:** [https://app-review-insights-analyser-roan.vercel.app/](https://app-review-insights-analyser-roan.vercel.app/)

## ?? Overview
Product, Growth, and Support teams need to know exactly what users are complaining about to prioritize their roadmaps effectively. However, manually reading, categorizing, and summarizing thousands of App Store and Google Play reviews every week is a highly manual, time-consuming process.

This project is a fully automated intelligence pipeline that extracts raw mobile app reviews and transforms them into a clean, actionable one-page weekly pulse for leadership and product teams.

## ?? Screenshots

![Dashboard Configuration](docs/screenshot1.png)

![Dashboard Overview](docs/screenshot2.png)

![Pipeline Execution](docs/screenshot3.png)

## ??? The Workflow
1. **Data Ingestion:** Automatically scrapes the latest 8–12 weeks of reviews from both the App Store and Google Play.
2. **Categorization:** Processes the raw data and groups the feedback into a maximum of 5 critical themes.
3. **Synthesis:** Uses Llama-3.3-70b to generate a highly scannable, one-page weekly note containing the top 3 themes, 3 real user quotes, and 3 immediate action ideas.
4. **Distribution:** Automatically drafts an email containing the weekly note so leadership has a quick health pulse waiting in their inbox.

## ?? How to re-run for a new week
To run the pipeline for a new week:
1. Open the UI Prototype (Vercel Link).
2. Go to the **Run Pipeline** (Rocket Icon) tab.
3. Click the **Run New Week** button to trigger the Python backend API (hosted on Render).
4. The pipeline will automatically fetch the latest reviews, group them into themes, generate the weekly note, and create a new email draft.
5. Check the **Weekly Note** and **Email Draft** tabs to see the updated insights.

## ?? Theme Legend
* **UI/UX Issues**: Complaints about app freezing, blank screens, and navigation issues.
* **Onboarding & KYC**: Friction during account creation, document verification delays.
* **Payments & Transactions**: Issues with money transfers, failed payments, and pending statuses.
* **Customer Support**: Lack of response from support, poor customer service experience.
* **Feature Requests**: Requests for new tools, dark mode, or better expense tracking.

---
*Built with ?? using Generative AI, Python, and Llama 3.*
