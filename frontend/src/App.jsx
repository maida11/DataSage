import { useState, useRef } from "react";
import axios from "axios";
import "./App.css";

const API = "http://localhost:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API}/upload`, formData);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.message || "Something went wrong. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadChart = async (chartPath) => {
    try {
      const res = await fetch(`${API}${chartPath}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = chartPath.split("/").pop();
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download chart", err);
    }
  };

  return (
    <div className="landing-page">
      {/* Floating Dark Navbar */}
<nav className="navbar">
        <div className="nav-brand">DataSage</div>
        
        <div className="nav-actions">
          <ul className="nav-links">
          {/* Label */}
          <li className="nav-label">Let's Connect:</li>
          <li className="nav-item-flex">
            <a href="https://github.com/maida11" target="_blank" rel="noopener noreferrer" className="social-link">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.6.113.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
              GitHub
            </a>
          </li>

          {/* LinkedIn Link */}
          <li className="nav-item-flex">
            {/* Make sure to put your actual LinkedIn URL in the href below! */}
            <a href="https://linkedin.com/in/maidashahzad11" target="_blank" rel="noopener noreferrer" className="social-link">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
              </svg>
              LinkedIn
            </a>
          </li>

        </ul>
        </div>
      </nav>

      <main className="hero">
        {/* Trust Badge */}
        <div className="trust-badge">
          <div className="avatars">
            <div className="avatar a1"></div>
            <div className="avatar a2"></div>
            <div className="avatar a3"></div>
          </div>
          <span>Trusted by data teams worldwide</span>
        </div>

        {/* Headlines */}
        <h1 className="hero-title">
          The AI data analyst for <br />
          <span className="hero-highlight">Insights at a Glance</span>
        </h1>
        
        <p className="hero-subtitle">
          Upload your messy CSV, generate visulaizations, charts and a processed csv.
        </p>

        {/* Call to Actions */}
        <div className="cta-group">
          <button 
            className="btn-primary-large" 
            onClick={() => fileInputRef.current.click()}
          >
            {file ? "Change Dataset" : "Upload Dataset"} →
          </button>
          
        </div>
        <p className="microcopy">No credit card required</p>

        {/* Input Bar (Acts as the file processor) */}
        <div className="action-bar-container">
          <input
            type="file"
            accept=".csv"
            ref={fileInputRef}
            onChange={(e) => setFile(e.target.files[0])}
            style={{ display: "none" }}
          />
          <div className="upload-bar">
             <span className="file-status">
               {file ? `Ready to process: ${file.name}` : "Upload a .csv file to begin..."}
             </span>
             <button 
               className="send-btn" 
               disabled={!file || loading} 
               onClick={handleUpload}
             >
               {loading ? "⌛" : "➤"}
             </button>
          </div>
        </div>

        {/* Loading & Error States */}
        {loading && <p className="status-text">Agents are analyzing your data. Come back after 5 mins.</p>}
        {error && <p className="error-text">{error}</p>}

        {/* Results Area */}
        {result && (
          <div className="results-container">
            <section className="result-card">
              <h3>Agent Logs</h3>
              <pre className="logs-box">{result.logs}</pre>
            </section>

            {result.cleaned_csv && (
              <section className="result-card flex-between">
                <h3>Cleaned Dataset Ready</h3>
                <a href={`${API}${result.cleaned_csv}`} download className="btn-success">
                  Download CSV
                </a>
              </section>
            )}

            {result.charts && result.charts.length > 0 && (
              <section className="result-card">
                <h3>Generated Charts</h3>
                <div className="chart-grid">
                  {result.charts.map((chart, i) => (
                    <div key={i} className="chart-item">
                    <img src={`${API}${chart}`} alt={chart} />
                    <p className="chart-name">{chart.split("/").pop().replace(".png", "").replaceAll("_", " ")}</p>
                    <button onClick={() => handleDownloadChart(chart)} className="btn-small">
                      Download
                    </button>
                  </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  );
}