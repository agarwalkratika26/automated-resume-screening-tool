# Next.js Recruiter Dashboard

This is the interactive frontend for the **Automated Resume Screening Tool**, built with Next.js 14 (App Router), TypeScript, and TailwindCSS.

## Features
- **Job Description Selector:** Browse benchmark job descriptions or review required/preferred skills.
- **Candidate Scoreboard:** View ranked candidate scorecards with match percentages and fit badges.
- **Multi-Factor Breakdown:** Inspect points awarded for Required Skills, Preferred Skills, TF-IDF Cosine Similarity, and Years of Experience.
- **Skill Gap Identification:** Instant visual display of matched vs. missing skills.
- **Hybrid Online/Offline Engine:** Seamlessly connects to the FastAPI backend (`http://127.0.0.1:8000`), with deterministic fallback simulation for instant standalone demonstration.

## Running the Dashboard

### Prerequisites
- Node.js 18.x or higher
- npm or pnpm or yarn

### Development Mode
```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at [http://localhost:3000](http://localhost:3000).

### Build for Production
```bash
npm run build
npm run start
```
