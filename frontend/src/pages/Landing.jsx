import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../App.css";

const features = [
  {
    icon: "🔍",
    title: "Intelligent Extraction",
    description: "AI-powered extraction agent identifies AYUSH disease terms from clinical notes with high accuracy using advanced NLP models.",
  },
  {
    icon: "🗺️",
    title: "ICD-11 Mapping",
    description: "Automated mapping to WHO ICD-11 codes through real-time API integration and curated deterministic mappings for 1200+ terms.",
  },
  {
    icon: "✅",
    title: "Validation & Confidence",
    description: "Multi-agent validation system provides confidence scores and flags cases requiring human review for quality assurance.",
  },
  {
    icon: "📤",
    title: "FHIR Export",
    description: "Generate ABDM-compliant FHIR Condition resources ready for seamless integration with India's health stack.",
  },
  {
    icon: "🔒",
    title: "Enterprise Security",
    description: "End-to-end encryption, HIPAA-compliant data handling, and role-based access control for healthcare environments.",
  },
  {
    icon: "📊",
    title: "Audit Trail",
    description: "Complete audit logging of all mappings, validations, and exports for regulatory compliance and traceability.",
  },
];

const workflowSteps = [
  {
    step: "01",
    title: "Extract AYUSH Term",
    description: "Our extraction agent analyzes clinical text to identify traditional medicine terminology.",
  },
  {
    step: "02",
    title: "Map to ICD-11",
    description: "Mapping agent searches WHO ICD-11 API and deterministic database for accurate code matching.",
  },
  {
    step: "03",
    title: "Validate & Score",
    description: "Validation agent evaluates mapping confidence and flags cases requiring expert review.",
  },
  {
    step: "04",
    title: "Export to ABDM",
    description: "Output agent generates FHIR-compliant resources for direct push to ABDM health stack.",
  },
];

const integrations = [
  { name: "WHO ICD-11", logo: "🌐" },
  { name: "ABDM", logo: "🏥" },
  { name: "NAMASTE", logo: "📋" },
  { name: "FHIR", logo: "⚡" },
];

const useCases = [
  {
    title: "Clinical Documentation",
    description: "Streamline patient records with automated ICD-11 coding for AYUSH diagnoses.",
  },
  {
    title: "EHR Integration",
    description: "Seamlessly integrate traditional medicine data into modern electronic health records.",
  },
  {
    title: "Research & Analytics",
    description: "Enable large-scale research by standardizing AYUSH terminology across datasets.",
  },
  {
    title: "Regulatory Compliance",
    description: "Meet government reporting requirements with ABDM-ready FHIR exports.",
  },
];

const stats = [
  { value: "1200+", label: "Mapped AYUSH Terms" },
  { value: "99.2%", label: "Uptime SLA" },
  { value: "<2s", label: "Average Response" },
  { value: "HIPAA", label: "Compliant" },
];

const navLinks = [
  { label: "Home", href: "#home" },
  { label: "Features", href: "#features" },
  { label: "Pipeline", href: "#pipeline" },
  { label: "Docs", href: "#docs" },
  { label: "Support", href: "#support" },
];

function Landing() {
  const [theme, setTheme] = useState("dark");
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return (
    <div className="page" id="home">
      <header className="nav">
        <div className="brand">
          <span className="logo" aria-hidden>
            <img src="/logo.svg" alt="" />
          </span>
          <span>AYUSH‑ICD Bridge</span>
        </div>
        <nav>
          {navLinks.map((link) => (
            <a key={link.label} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
        <div className="nav-actions">
          <button
            className="theme-toggle icon"
            aria-label="Toggle theme"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <img
              src={theme === "dark" ? "/icons/sun.svg" : "/icons/moon.svg"}
              alt=""
            />
          </button>
          {isAuthenticated ? (
            <Link to="/dashboard" className="button-link primary">
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="button-link ghost">
                Sign in
              </Link>
              <Link to="/register" className="button-link primary">
                Sign up
              </Link>
            </>
          )}
        </div>
      </header>

      <main>
        <section className="hero">
          <p className="pill">Enterprise-Grade AYUSH Intelligence Platform</p>
          <h1>
            Transform Traditional Medicine Data into{" "}
            <span>Modern Healthcare Standards</span>
          </h1>
          <p className="subtitle">
            AYUSHAgent bridges the gap between traditional AYUSH medicine and modern healthcare systems. 
            Our agentic AI pipeline automatically extracts, maps, validates, and exports AYUSH diagnoses 
            to ICD-11 codes with FHIR compliance for seamless ABDM integration.
          </p>
          <div className="hero-actions">
            {isAuthenticated ? (
              <Link to="/dashboard" className="button-link primary">
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link to="/register" className="button-link primary">
                  Start Free Trial
                </Link>
                <button className="ghost">Schedule Demo</button>
                <button className="ghost">View Documentation</button>
              </>
            )}
          </div>
          <div className="trust-badges">
            <span className="badge">HIPAA Compliant</span>
            <span className="badge">ISO 27001</span>
            <span className="badge">ABDM Certified</span>
          </div>
        </section>

        <section className="stats-section">
          <div className="stats-grid">
            {stats.map((stat, idx) => (
              <div key={idx} className="stat-card">
                <p className="stat-value">{stat.value}</p>
                <p className="stat-label">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="features-section" id="features">
          <div className="section-header">
            <p className="pill subtle">Core Capabilities</p>
            <h2>Powered by Agentic AI Architecture</h2>
            <p className="section-description">
              Four specialized AI agents work in coordination to deliver accurate, validated, 
              and compliant mappings from AYUSH terminology to ICD-11 standards.
            </p>
          </div>
          <div className="features-grid">
            {features.map((feature, idx) => (
              <div key={idx} className="feature-card">
                <div className="feature-icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="workflow-section" id="pipeline">
          <div className="section-header">
            <p className="pill subtle">How It Works</p>
            <h2>End-to-End Agentic Pipeline</h2>
            <p className="section-description">
              From clinical text input to ABDM-ready FHIR export in four coordinated steps.
            </p>
          </div>
          <div className="workflow-grid">
            {workflowSteps.map((step, idx) => (
              <div key={idx} className="workflow-card">
                <div className="workflow-step">{step.step}</div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="integrations-section" id="docs">
          <div className="section-header">
            <p className="pill subtle">Seamless Integrations</p>
            <h2>Built for Healthcare Interoperability</h2>
          </div>
          <div className="integrations-grid">
            {integrations.map((integration, idx) => (
              <div key={idx} className="integration-card">
                <div className="integration-logo">{integration.logo}</div>
                <p>{integration.name}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="usecases-section">
          <div className="section-header">
            <p className="pill subtle">Use Cases</p>
            <h2>Trusted by Healthcare Organizations</h2>
          </div>
          <div className="usecases-grid">
            {useCases.map((useCase, idx) => (
              <div key={idx} className="usecase-card">
                <h3>{useCase.title}</h3>
                <p>{useCase.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="cta-section" id="support">
          <div className="cta-card">
            <h2>Ready to Transform Your AYUSH Practice?</h2>
            <p>Join leading healthcare providers using AYUSHAgent for compliant, accurate, and efficient diagnosis mapping.</p>
            <div className="hero-actions">
              {isAuthenticated ? (
                <Link to="/dashboard" className="button-link primary">
                  Go to Dashboard
                </Link>
              ) : (
                <>
                  <Link to="/register" className="button-link primary">
                    Get Started Free
                  </Link>
                  <button className="ghost">Contact Sales</button>
                </>
              )}
            </div>
          </div>
        </section>
      </main>

      <footer>
        <div className="footer-content">
          <div className="footer-brand">
            <div className="brand">
              <span className="logo" aria-hidden>
                <img src="/logo.svg" alt="" />
              </span>
              <span>AYUSH‑ICD Bridge</span>
            </div>
            <p>Bridging traditional medicine with modern healthcare standards through AI.</p>
          </div>
          <div className="footer-columns">
            <div className="footer-column">
              <h4>Product</h4>
              <a href="#">Features</a>
              <a href="#">Pricing</a>
              <a href="#">API Documentation</a>
              <a href="#">Changelog</a>
            </div>
            <div className="footer-column">
              <h4>Resources</h4>
              <a href="#">Documentation</a>
              <a href="#">Guides</a>
              <a href="#">Case Studies</a>
              <a href="#">Support</a>
            </div>
            <div className="footer-column">
              <h4>Company</h4>
              <a href="#">About</a>
              <a href="#">Blog</a>
              <a href="#">Careers</a>
              <a href="#">Contact</a>
            </div>
            <div className="footer-column">
              <h4>Legal</h4>
              <a href="#">Privacy Policy</a>
              <a href="#">Terms of Service</a>
              <a href="#">Security</a>
              <a href="#">Compliance</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© {new Date().getFullYear()} AYUSHAgent. All rights reserved.</p>
          <div className="footer-links">
            <a href="#">Privacy</a>
            <a href="#">Security</a>
            <a href="#">Docs</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Landing;

