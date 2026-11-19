"use client";

import React, { useState, useEffect, useRef } from "react";

interface JobDescription {
  id: string;
  title: string;
  department: string;
  experience_years_required: number;
  required_skills: string[];
  preferred_skills: string[];
  description: string;
}

interface SkillBreakdown {
  matched_required_skills: string[];
  missing_required_skills: string[];
  matched_preferred_skills: string[];
  missing_preferred_skills: string[];
  required_skill_match_ratio: number;
  preferred_skill_match_ratio: number;
}

interface CandidateScore {
  rank: number;
  filename: string;
  candidate_name: string;
  total_score: number;
  fit_category: string;
  required_skill_score: number;
  preferred_skill_score: number;
  tfidf_similarity_score?: number;
  semantic_similarity_score?: number;
  experience_score: number;
  estimated_experience_years?: number | null;
  skill_breakdown: SkillBreakdown;
  extracted_skills: string[];
  isUploaded?: boolean;
}

const DEFAULT_JOBS: JobDescription[] = [
  {
    id: "JD-001",
    title: "Senior AI / Machine Learning Engineer",
    department: "Artificial Intelligence",
    experience_years_required: 5,
    required_skills: ["Python", "PyTorch", "Machine Learning", "Natural Language Processing", "FastAPI", "Docker"],
    preferred_skills: ["Transformers", "LangChain", "Kubernetes", "AWS", "PostgreSQL", "MLOps"],
    description: "Lead the architecture and deployment of large language model (LLM) services and production NLP pipelines with FastAPI and Docker on AWS."
  },
  {
    id: "JD-002",
    title: "Full Stack Software Engineer (Next.js / Python)",
    department: "Product Engineering",
    experience_years_required: 3,
    required_skills: ["TypeScript", "React", "Next.js", "Python", "FastAPI", "PostgreSQL"],
    preferred_skills: ["TailwindCSS", "Docker", "REST APIs", "AWS", "Git", "Jest"],
    description: "Build modern web applications with Next.js App Router frontends and high-performance Python FastAPI backends."
  },
  {
    id: "JD-003",
    title: "Data Scientist",
    department: "Data & Analytics",
    experience_years_required: 3,
    required_skills: ["Python", "SQL", "Scikit-learn", "Pandas", "Machine Learning", "A/B Testing"],
    preferred_skills: ["Tableau", "BigQuery", "XGBoost", "Statistics", "Docker", "Airflow"],
    description: "Design rigorous A/B experiments and train predictive machine learning models across product datasets."
  }
];

export default function RecruiterDashboard() {
  const [jobs, setJobs] = useState<JobDescription[]>(DEFAULT_JOBS);
  const [selectedJobId, setSelectedJobId] = useState<string>("JD-001");
  const [candidates, setCandidates] = useState<CandidateScore[]>([]);
  const [isLoadingBatch, setIsLoadingBatch] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [stagedFile, setStagedFile] = useState<File | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"all" | "strong" | "moderate">("all");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const currentJob = jobs.find((j) => j.id === selectedJobId) || jobs[0];

  // Check backend health & fetch jobs on load
  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/health")
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") {
          setBackendOnline(true);
          fetch("http://127.0.0.1:8000/api/jobs")
            .then((r) => r.json())
            .then((jobList) => {
              if (Array.isArray(jobList) && jobList.length > 0) setJobs(jobList);
            })
            .catch(() => {});
        }
      })
      .catch(() => setBackendOnline(false));
  }, []);

  // Stage a file when selected (does NOT submit yet)
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setUploadSuccess(null);

    // 1. Client-side extension validation
    const ext = file.name.split(".").pop()?.toLowerCase();
    const allowed = ["txt", "pdf", "docx"];
    if (!ext || !allowed.includes(ext)) {
      setUploadError(`Unsupported file format '.${ext || "unknown"}'. Only .txt, .pdf, and .docx are supported.`);
      setStagedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    // 2. Client-side file size validation (5MB max)
    const MAX_BYTES = 5 * 1024 * 1024;
    if (file.size > MAX_BYTES) {
      setUploadError(`File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds the 5MB maximum limit.`);
      setStagedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    // Stage the file for upload
    setStagedFile(file);
  };

  const handleClearStagedFile = () => {
    setStagedFile(null);
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Submit the staged resume file to POST /api/screen
  const handleSubmitUpload = async () => {
    if (!stagedFile) {
      setUploadError("Please select a candidate resume file (.txt, .pdf, or .docx) to stage first.");
      fileInputRef.current?.click();
      return;
    }

    setUploadError(null);
    setUploadSuccess(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", stagedFile);
      formData.append("job_id", selectedJobId);

      const response = await fetch("http://127.0.0.1:8000/api/screen", {
        method: "POST",
        body: formData,
      });

      if (response.status === 413) {
        throw new Error("Upload rejected: File exceeds the maximum allowed size of 5MB.");
      }

      if (!response.ok) {
        let msg = `Screening failed with status code ${response.status}.`;
        try {
          const jsonErr = await response.json();
          if (jsonErr.detail) msg = jsonErr.detail;
        } catch {}
        throw new Error(msg);
      }

      const score: CandidateScore = await response.json();
      score.isUploaded = true;

      // Add uploaded candidate to comparison leaderboard
      setCandidates((prev) => {
        const remaining = prev.filter((c) => c.filename !== score.filename);
        const updated = [score, ...remaining];
        updated.sort((a, b) => b.total_score - a.total_score);
        updated.forEach((c, idx) => { c.rank = idx + 1; });
        return updated;
      });

      setBackendOnline(true);
      setUploadSuccess(`Successfully screened "${score.candidate_name}" (${score.total_score}% fit) against ${currentJob.title}!`);
      setStagedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err: any) {
      setUploadError(err.message || "Could not connect to FastAPI server at http://127.0.0.1:8000. Start backend with 'python main.py --serve'.");
    } finally {
      setIsUploading(false);
    }
  };

  // Run batch demo screening on bundled sample resumes in resumes/sample/
  const runBundledSampleDemo = async () => {
    setIsLoadingBatch(true);
    setUploadError(null);
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/screen/batch?job_id=${selectedJobId}`,
        { method: "POST" }
      );
      if (response.ok) {
        const data = await response.json();
        setCandidates(data.ranked_candidates);
        setBackendOnline(true);
      } else {
        throw new Error("Backend batch error");
      }
    } catch {
      // Deterministic client simulation if backend is offline
      simulateOfflineScreening(currentJob);
    } finally {
      setIsLoadingBatch(false);
    }
  };

  const simulateOfflineScreening = (job: JobDescription) => {
    const mockProfiles = [
      {
        name: "Sarah Chen",
        file: "sarah_chen_senior_ai_engineer.txt",
        skills: ["Python", "PyTorch", "Machine Learning", "Natural Language Processing", "FastAPI", "Docker", "Transformers", "LangChain", "Kubernetes", "AWS", "PostgreSQL"],
        exp: 6.0
      },
      {
        name: "Alex Rivera",
        file: "alex_rivera_fullstack_developer.txt",
        skills: ["TypeScript", "React", "Next.js", "Python", "FastAPI", "PostgreSQL", "TailwindCSS", "Docker", "REST APIs", "AWS", "Git", "Jest"],
        exp: 4.5
      },
      {
        name: "Priya Sharma",
        file: "priya_sharma_data_scientist.txt",
        skills: ["Python", "SQL", "Scikit-learn", "Pandas", "Machine Learning", "A/B Testing", "Tableau", "BigQuery", "XGBoost", "Statistics", "Docker"],
        exp: 3.5
      },
      {
        name: "Marcus Vance",
        file: "marcus_vance_cloud_devops_engineer.txt",
        skills: ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "GitHub Actions", "Prometheus", "Linux", "Python", "Bash"],
        exp: 5.5
      },
      {
        name: "Elena Rostova",
        file: "elena_rostova_junior_python_developer.txt",
        skills: ["Python", "JavaScript", "SQL", "Flask", "FastAPI", "Git"],
        exp: 1.5
      }
    ];

    const scored = mockProfiles.map((p) => {
      const matchedReq = job.required_skills.filter((s) => p.skills.some((ps) => ps.toLowerCase() === s.toLowerCase()));
      const missingReq = job.required_skills.filter((s) => !matchedReq.includes(s));
      const matchedPref = job.preferred_skills.filter((s) => p.skills.some((ps) => ps.toLowerCase() === s.toLowerCase()));
      const missingPref = job.preferred_skills.filter((s) => !matchedPref.includes(s));

      const reqScore = Math.round((matchedReq.length / job.required_skills.length) * 40 * 10) / 10;
      const prefScore = Math.round((matchedPref.length / (job.preferred_skills.length || 1)) * 20 * 10) / 10;
      const expRatio = Math.min(1.0, p.exp / job.experience_years_required);
      const expScore = Math.round(expRatio * 15 * 10) / 10;
      const simScore = Math.round((reqScore / 40) * 23.5 * 10) / 10;

      const total = Math.min(100, Math.round((reqScore + prefScore + expScore + simScore) * 10) / 10);
      const fit = total >= 75 ? "Strong Match" : total >= 50 ? "Moderate Match" : "Weak Match";

      return {
        rank: 0,
        filename: p.file,
        candidate_name: p.name,
        total_score: total,
        fit_category: fit,
        required_skill_score: reqScore,
        preferred_skill_score: prefScore,
        tfidf_similarity_score: simScore,
        semantic_similarity_score: simScore,
        experience_score: expScore,
        estimated_experience_years: p.exp,
        skill_breakdown: {
          matched_required_skills: matchedReq,
          missing_required_skills: missingReq,
          matched_preferred_skills: matchedPref,
          missing_preferred_skills: missingPref,
          required_skill_match_ratio: matchedReq.length / job.required_skills.length,
          preferred_skill_match_ratio: matchedPref.length / (job.preferred_skills.length || 1)
        },
        extracted_skills: p.skills,
        isUploaded: false
      };
    });

    scored.sort((a, b) => b.total_score - a.total_score);
    scored.forEach((c, i) => { c.rank = i + 1; });
    setCandidates(scored);
  };

  const filteredCandidates = candidates.filter((c) => {
    if (activeTab === "strong") return c.fit_category === "Strong Match";
    if (activeTab === "moderate") return c.fit_category === "Moderate Match";
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-md shadow-blue-200">
              RS
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                Automated Resume Screening Tool
              </h1>
              <p className="text-sm text-slate-500">
                Recruiter Intelligence Dashboard • Multi-Factor Match Scoring &amp; TF-IDF Ranking
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
              backendOnline
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : "bg-amber-50 text-amber-700 border-amber-200"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendOnline ? "bg-emerald-500" : "bg-amber-500 animate-pulse"
              }`}
            />
            {backendOnline ? "FastAPI Connected" : "Local Engine Mode"}
          </span>

          <button
            onClick={runBundledSampleDemo}
            disabled={isLoadingBatch}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-semibold text-xs shadow-sm transition-all"
          >
            {isLoadingBatch ? "Evaluating Samples..." : "⚡ Run Bundled Batch Demo"}
          </button>
        </div>
      </header>

      {/* Target Job Profile Selector */}
      <section className="mt-8 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">1. Target Job Profile</h2>
            <p className="text-xs text-slate-500">
              Select the benchmark job specification to evaluate uploaded or sample candidate resumes against.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {jobs.map((job) => (
              <button
                key={job.id}
                onClick={() => {
                  setSelectedJobId(job.id);
                  if (candidates.length > 0 && !candidates.some((c) => c.isUploaded)) {
                    simulateOfflineScreening(job);
                  }
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                  selectedJobId === job.id
                    ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                    : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                }`}
              >
                {job.id}: {job.title}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 text-xs space-y-2">
          <div className="flex flex-wrap gap-4 text-slate-600">
            <span><strong>Department:</strong> {currentJob.department}</span>
            <span><strong>Experience Required:</strong> {currentJob.experience_years_required} Years</span>
          </div>
          <div>
            <strong className="text-slate-700">Mandatory Skills:</strong>{" "}
            <span className="text-blue-700">{currentJob.required_skills.join(" • ")}</span>
          </div>
          <div>
            <strong className="text-slate-700">Preferred Skills:</strong>{" "}
            <span className="text-slate-600">{currentJob.preferred_skills.join(" • ")}</span>
          </div>
        </div>
      </section>

      {/* Resume File Upload Section (Staging & Submission) */}
      <section className="mt-6 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-bold text-slate-900">2. Upload &amp; Screen Resume</h2>
            <p className="text-xs text-slate-500">
              Select a resume to stage it, then click <strong>"Upload &amp; Screen"</strong> to evaluate against <strong>{currentJob.id} ({currentJob.title})</strong>.
            </p>
          </div>
          <span className="text-xs text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1 rounded-full self-start md:self-auto">
            Supported: .txt, .pdf, .docx • Max 5MB
          </span>
        </div>

        {uploadError && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center justify-between">
            <span>⚠️ {uploadError}</span>
            <button onClick={() => setUploadError(null)} className="text-rose-500 hover:text-rose-800 font-bold ml-2">✕</button>
          </div>
        )}

        {uploadSuccess && (
          <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between">
            <span>✓ {uploadSuccess}</span>
            <button onClick={() => setUploadSuccess(null)} className="text-emerald-600 hover:text-emerald-900 font-bold ml-2">✕</button>
          </div>
        )}

        {/* Staged file visual badge */}
        {stagedFile && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-blue-900">
              <span className="font-semibold">📄 Staged Resume:</span>
              <span className="font-mono">{stagedFile.name}</span>
              <span className="text-blue-600">({(stagedFile.size / 1024).toFixed(1)} KB)</span>
            </div>
            <button
              onClick={handleClearStagedFile}
              className="text-blue-600 hover:text-blue-900 font-medium text-xs underline"
            >
              Clear
            </button>
          </div>
        )}

        <div className="mt-4 flex flex-col sm:flex-row items-center gap-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={handleFileSelect}
            disabled={isUploading}
            className="block w-full text-xs text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 border border-slate-200 rounded-xl cursor-pointer bg-slate-50 p-2"
          />

          <button
            onClick={handleSubmitUpload}
            disabled={isUploading || !stagedFile}
            className={`w-full sm:w-auto shrink-0 px-6 py-2.5 rounded-xl text-xs font-semibold shadow-sm transition-all flex items-center justify-center gap-2 ${
              stagedFile && !isUploading
                ? "bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
                : "bg-slate-200 text-slate-400 cursor-not-allowed"
            }`}
          >
            {isUploading ? "Screening Upload..." : "Upload & Screen"}
          </button>
        </div>
      </section>

      {/* Analytics Overview Cards */}
      {candidates.length > 0 && (
        <section className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
            <span className="text-xs font-medium text-slate-500">Total Evaluated</span>
            <p className="text-2xl font-extrabold text-slate-900">{candidates.length}</p>
          </div>
          <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
            <span className="text-xs font-medium text-emerald-600">Strong Matches</span>
            <p className="text-2xl font-extrabold text-emerald-600">
              {candidates.filter((c) => c.fit_category === "Strong Match").length}
            </p>
          </div>
          <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
            <span className="text-xs font-medium text-blue-600">Top Match Score</span>
            <p className="text-2xl font-extrabold text-blue-600">{candidates[0]?.total_score}%</p>
          </div>
          <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
            <span className="text-xs font-medium text-purple-600">Leading Candidate</span>
            <p className="text-base font-bold text-slate-900 truncate">
              {candidates[0]?.candidate_name}
            </p>
          </div>
        </section>
      )}

      {/* Candidate Scorecard Leaderboard */}
      <section className="mt-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              3. Candidate Leaderboard &amp; Scorecards ({filteredCandidates.length})
            </h2>
            <p className="text-xs text-slate-500">
              Ranked results for {currentJob.title}. Includes both uploaded resumes and bundled benchmark samples.
            </p>
          </div>

          {candidates.length > 0 && (
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-medium self-start sm:self-auto">
              <button
                onClick={() => setActiveTab("all")}
                className={`px-3 py-1 rounded-md transition-all ${
                  activeTab === "all" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                }`}
              >
                All ({candidates.length})
              </button>
              <button
                onClick={() => setActiveTab("strong")}
                className={`px-3 py-1 rounded-md transition-all ${
                  activeTab === "strong" ? "bg-white text-emerald-700 shadow-sm" : "text-slate-600"
                }`}
              >
                Strong Matches
              </button>
              <button
                onClick={() => setActiveTab("moderate")}
                className={`px-3 py-1 rounded-md transition-all ${
                  activeTab === "moderate" ? "bg-white text-amber-700 shadow-sm" : "text-slate-600"
                }`}
              >
                Moderate Matches
              </button>
            </div>
          )}
        </div>

        {candidates.length === 0 ? (
          <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center">
            <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-3 font-bold text-xl">
              📄
            </div>
            <h3 className="text-base font-bold text-slate-800">No Candidates Screened Yet</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-5">
              Select a resume to stage it and click <strong>"Upload &amp; Screen"</strong>, or run the bundled sample demo.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 shadow-sm"
              >
                Select Resume to Stage
              </button>
              <button
                onClick={runBundledSampleDemo}
                className="px-4 py-2 bg-slate-800 text-white rounded-lg text-xs font-semibold hover:bg-slate-700 shadow-sm"
              >
                ⚡ Run Bundled Batch Demo
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredCandidates.map((candidate) => (
              <div
                key={candidate.filename}
                className={`bg-white border rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow ${
                  candidate.isUploaded ? "border-blue-300 ring-1 ring-blue-100" : "border-slate-200"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-full bg-slate-900 text-white font-bold text-sm flex items-center justify-center shrink-0">
                      #{candidate.rank}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-slate-900">
                          {candidate.candidate_name}
                        </h3>
                        {candidate.isUploaded ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                            Uploaded
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600">
                            Sample
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 font-mono">{candidate.filename}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-xs text-slate-500">Overall Match</span>
                      <p className="text-2xl font-black text-slate-900">{candidate.total_score}%</p>
                    </div>

                    <span
                      className={`px-3 py-1.5 rounded-full text-xs font-bold ${
                        candidate.fit_category === "Strong Match"
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : candidate.fit_category === "Moderate Match"
                          ? "bg-amber-100 text-amber-800 border border-amber-300"
                          : "bg-rose-100 text-rose-800 border border-rose-300"
                      }`}
                    >
                      {candidate.fit_category}
                    </span>
                  </div>
                </div>

                {/* Score breakdown metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 my-4 text-xs">
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-slate-500">Required Skills</span>
                    <p className="font-bold text-slate-800">{candidate.required_skill_score} / 40.0</p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-slate-500">Preferred Skills</span>
                    <p className="font-bold text-slate-800">{candidate.preferred_skill_score} / 20.0</p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-slate-500">TF-IDF Cosine Similarity</span>
                    <p className="font-bold text-slate-800">
                      {candidate.tfidf_similarity_score ?? candidate.semantic_similarity_score ?? 0} / 25.0
                    </p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-slate-500">Experience Alignment</span>
                    <p className="font-bold text-slate-800">
                      {candidate.experience_score} / 15.0 ({candidate.estimated_experience_years != null ? `${candidate.estimated_experience_years} yrs` : "Unknown"})
                    </p>
                  </div>
                </div>

                {/* Skill Badges */}
                <div className="space-y-2 text-xs">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="font-semibold text-emerald-700 mr-1">✓ Matched:</span>
                    {candidate.skill_breakdown.matched_required_skills.map((s) => (
                      <span key={s} className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {s}
                      </span>
                    ))}
                    {candidate.skill_breakdown.matched_preferred_skills.map((s) => (
                      <span key={s} className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                        {s} (pref)
                      </span>
                    ))}
                  </div>

                  {candidate.skill_breakdown.missing_required_skills.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="font-semibold text-rose-600 mr-1">✕ Missing Required:</span>
                      {candidate.skill_breakdown.missing_required_skills.map((s) => (
                        <span key={s} className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
