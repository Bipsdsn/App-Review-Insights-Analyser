# App Review Insights Analyser

**Prototype Link:** [https://app-review-insights-analyser-roan.vercel.app/](https://app-review-insights-analyser-roan.vercel.app/)

## Overview
This tool turns recent App Store + Play Store reviews into a one-page weekly pulse containing:
- Top 5 themes
- Real user quotes
- Three action ideas
- An automated draft email containing this weekly note.

## How to re-run for a new week
To run the pipeline for a new week:
1. Open the UI Prototype (Vercel Link).
2. Go to the **Run Pipeline** (Rocket Icon) tab.
3. Click the **Run New Week** button to trigger the Python backend API (hosted on Render).
4. The pipeline will automatically fetch the latest reviews from the App Store and Google Play (using pp-store-scraper and google-play-scraper).
5. It groups reviews into a maximum of 5 themes, generates the weekly note, and creates a new email draft.
6. Check the **Weekly Note** and **Email Draft** tabs to see the updated insights.

## Theme Legend
* **UI/UX Issues**: Complaints about app freezing, blank screens, and navigation issues.
* **Onboarding & KYC**: Friction during account creation, document verification delays.
* **Payments & Transactions**: Issues with money transfers, failed payments, and pending statuses.
* **Customer Support**: Lack of response from support, poor customer service experience.
* **Feature Requests**: Requests for new tools, dark mode, or better expense tracking.

(See Theme_Legend.md for the dynamically generated version).
