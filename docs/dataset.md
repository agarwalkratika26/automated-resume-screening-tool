# Dataset & Data Fixtures

## 1. Synthetic Resume Corpus (`resumes/sample/`)
To protect candidate privacy and ensure strict compliance with data protection policies, **zero real personal information is used**. All resumes are synthetically generated profiles representing realistic software engineering, data science, and infrastructure roles.

### Synthetic Candidate Profiles

| Filename | Inferred Name | Role Archetype | Key Proficiencies | Synthetic Exp |
| :--- | :--- | :--- | :--- | :--- |
| `sarah_chen_senior_ai_engineer.txt` | Sarah Chen | Senior AI/ML Engineer | Python, PyTorch, FastAPI, Docker, Transformers, LangChain, AWS | 6.0 yrs |
| `alex_rivera_fullstack_developer.txt` | Alex Rivera | Full Stack Developer | Next.js, React, TypeScript, Python, FastAPI, TailwindCSS, PostgreSQL | 4.5 yrs |
| `priya_sharma_data_scientist.txt` | Priya Sharma | Data Scientist | Python, SQL, Scikit-learn, Pandas, XGBoost, A/B Testing, Tableau | 3.5 yrs |
| `marcus_vance_cloud_devops_engineer.txt` | Marcus Vance | Cloud DevOps Engineer | AWS, Terraform, Docker, Kubernetes, CI/CD, Prometheus, Linux | 5.5 yrs |
| `elena_rostova_junior_python_developer.txt` | Elena Rostova | Junior Python Developer | Python, Flask, FastAPI, SQL, Git, HTML/CSS | 1.5 yrs |

---

## 2. Job Description Fixtures (`data/job_descriptions.json`)
The platform includes 3 standardized job specifications for benchmarking:

1. **`JD-001` — Senior AI / Machine Learning Engineer**
   - **Department:** Artificial Intelligence & Core Tech
   - **Required Experience:** 5.0 years
   - **Required Skills:** `Python`, `PyTorch`, `Machine Learning`, `Natural Language Processing`, `FastAPI`, `Docker`
   - **Preferred Skills:** `Transformers`, `LangChain`, `Kubernetes`, `AWS`, `PostgreSQL`, `MLOps`

2. **`JD-002` — Full Stack Software Engineer (Next.js / Python)**
   - **Department:** Product Engineering
   - **Required Experience:** 3.0 years
   - **Required Skills:** `TypeScript`, `React`, `Next.js`, `Python`, `FastAPI`, `PostgreSQL`
   - **Preferred Skills:** `TailwindCSS`, `Docker`, `REST APIs`, `AWS`, `Git`, `Jest`

3. **`JD-003` — Data Scientist**
   - **Department:** Data & Analytics
   - **Required Experience:** 3.0 years
   - **Required Skills:** `Python`, `SQL`, `Scikit-learn`, `Pandas`, `Machine Learning`, `A/B Testing`
   - **Preferred Skills:** `Tableau`, `BigQuery`, `XGBoost`, `Statistics`, `Docker`, `Airflow`

---

## 3. Skill Taxonomy & Alias Mapping (`data/skills.json`)
The vocabulary contains 7 major technical categories:
- **Programming Languages:** Python, TypeScript, JavaScript, SQL, C++, Java, Go, Rust, R, Bash, HTML5, CSS3.
- **Machine Learning & AI:** PyTorch, TensorFlow, Scikit-learn, Transformers, LangChain, OpenCV, XGBoost, RAG, LLMs.
- **Web & Frontend:** React, Next.js, TailwindCSS, Redux, styled-components, Vue, Angular.
- **Backend & APIs:** FastAPI, Flask, Django, Node.js, Express, REST APIs, GraphQL, Celery.
- **Databases:** PostgreSQL, MongoDB, Redis, Pinecone, Weaviate, BigQuery, SQLite, Prisma ORM.
- **Cloud & DevOps:** AWS, Docker, Kubernetes, Terraform, CI/CD, GitHub Actions, Helm, Prometheus.
- **Analytics & Data Science:** Pandas, NumPy, SciPy, Tableau, Power BI, A/B Testing, Airflow.

### Synonym & Alias Resolution Examples
- `nlp` $\rightarrow$ `Natural Language Processing`
- `k8s` $\rightarrow$ `Kubernetes`
- `postgres` $\rightarrow$ `PostgreSQL`
- `nextjs` / `next.js` $\rightarrow$ `Next.js`
- `sklearn` $\rightarrow$ `Scikit-learn`
- `rest api` / `restful apis` $\rightarrow$ `REST APIs`
