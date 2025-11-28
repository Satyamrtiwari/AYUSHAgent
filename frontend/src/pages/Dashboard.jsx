import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { patientAPI, diagnosisAPI, pipelineAPI } from '../services/api';
import PatientModal from '../components/PatientModal';
import './Dashboard.css';

function Dashboard() {
  const { user, logout } = useAuth();
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [diagnoses, setDiagnoses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pipelineState, setPipelineState] = useState(null);
  const [rawText, setRawText] = useState('');
  const [autoPush, setAutoPush] = useState(false);
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [creatingPatient, setCreatingPatient] = useState(false);
  const [agentProgress, setAgentProgress] = useState(null);
  const [patientError, setPatientError] = useState('');
  const [manualSelection, setManualSelection] = useState(null);
  const [manualReviewStatus, setManualReviewStatus] = useState({
    saving: false,
    success: null,
    error: null,
  });

  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      fetchDiagnoses(selectedPatient.id);
    }
  }, [selectedPatient]);

  const fetchPatients = async () => {
    try {
      const response = await patientAPI.list();
      setPatients(response.data);
      if (response.data.length > 0 && !selectedPatient) {
        setSelectedPatient(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  const fetchDiagnoses = async (patientId) => {
    try {
      const response = await diagnosisAPI.list();
      const filtered = response.data.filter((d) => d.patient === patientId);
      setDiagnoses(filtered);
    } catch (error) {
      console.error('Error fetching diagnoses:', error);
    }
  };

  const handleRunPipeline = async () => {
    if (!selectedPatient || !rawText.trim()) {
      alert('Please select a patient and enter clinical text');
      return;
    }

    setLoading(true);
    setAgentProgress({ stage: 'extraction', message: 'Extracting AYUSH term...', progress: 25 });
    setPipelineState(null);
    setManualSelection(null);
    setManualReviewStatus({ saving: false, success: null, error: null });

    // Simulate agent progress
    setTimeout(() => {
      setAgentProgress({ stage: 'mapping', message: 'Mapping to ICD-11 codes...', progress: 50 });
    }, 1000);

    setTimeout(() => {
      setAgentProgress({ stage: 'validation', message: 'Validating mapping confidence...', progress: 75 });
    }, 2000);

    try {
      const response = await pipelineAPI.run({
        patient_id: selectedPatient.id,
        raw_text: rawText,
        auto_push: autoPush,
      });

      setAgentProgress({ stage: 'complete', message: 'Pipeline completed successfully', progress: 100 });
      
      setTimeout(() => {
        setPipelineState({
          stage: 'complete',
          message: 'Pipeline completed successfully',
          result: response.data.result,
          diagnosis: response.data,
        });
        setAgentProgress(null);
        const candidates = response.data.result?.manual_review_candidates || [];
        if (candidates.length > 0) {
          const defaultPick =
            candidates.find((c) => c.code === response.data.result?.best?.code) || candidates[0];
          setManualSelection(defaultPick);
        }
        setManualReviewStatus({ saving: false, success: null, error: null });
      }, 500);

      await fetchDiagnoses(selectedPatient.id);
      setRawText('');
    } catch (error) {
      console.error('Pipeline error:', error);
      console.error('Error response:', error.response);
      
      setAgentProgress(null);
      
      let errorMessage = 'Pipeline execution failed';
      
      if (error.response?.data) {
        const data = error.response.data;
        if (typeof data === 'object') {
          errorMessage = data.error || data.message || JSON.stringify(data);
        } else if (typeof data === 'string') {
          errorMessage = data;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setPipelineState({
        stage: 'error',
        message: errorMessage,
        error: error.response?.data,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleManualReviewApply = async () => {
    if (!manualSelection || !pipelineState?.diagnosis?.diagnosis_id) {
      return;
    }
    setManualReviewStatus({ saving: true, success: null, error: null });
    try {
      await diagnosisAPI.partialUpdate(pipelineState.diagnosis.diagnosis_id, {
        icd_code: manualSelection.code,
        confidence_score: manualSelection.score ?? pipelineState.result?.confidence ?? 0.8,
        ayush_term: pipelineState.result?.ayush_term,
      });

      setPipelineState((prev) => {
        if (!prev?.result) return prev;
        return {
          ...prev,
          result: {
            ...prev.result,
            best: {
              ...(prev.result.best || {}),
              code: manualSelection.code,
              title: manualSelection.title,
            },
            confidence: manualSelection.score ?? prev.result.confidence,
            manual_review_selected: manualSelection,
            manual_review_applied: true,
          },
        };
      });
      setManualReviewStatus({ saving: false, success: 'Selection saved to diagnosis.', error: null });
      if (selectedPatient) {
        fetchDiagnoses(selectedPatient.id);
      }
    } catch (error) {
      console.error('Manual review update failed:', error);
      setManualReviewStatus({
        saving: false,
        success: null,
        error: 'Failed to save selection. Please retry.',
      });
    }
  };

  const handleCreatePatient = async (formData) => {
    setCreatingPatient(true);
    setPatientError('');
    try {
      await patientAPI.create({ 
        name: formData.name, 
        ayush_id: formData.ayush_id,
        age: parseInt(formData.age)
      });
      await fetchPatients();
      setShowPatientModal(false);
      setPatientError('');
    } catch (error) {
      // Debug: log the actual error
      console.error('Patient creation error:', error);
      console.error('Error response:', error.response);
      
      let errorMessage = 'Error creating patient';
      
      // Check response status
      const status = error.response?.status;
      const data = error.response?.data;
      const contentType = error.response?.headers?.['content-type'] || '';
      
      // Handle 400 Bad Request (validation errors)
      if (status === 400 && data) {
        if (typeof data === 'object' && !Array.isArray(data)) {
          // Django REST Framework error format
          const errors = [];
          let hasDuplicateError = false;
          
          for (const [key, value] of Object.entries(data)) {
            if (Array.isArray(value)) {
              const errorText = value.join(', ');
              const lowerText = errorText.toLowerCase();
              
              // ONLY show "already exists" if:
              // 1. The field is 'ayush_id' AND
              // 2. The error explicitly mentions "already exists" or "unique"
              if (key === 'ayush_id' && 
                  (lowerText.includes('already exists') || 
                   lowerText.includes('unique') ||
                   lowerText.includes('duplicate'))) {
                errors.push(`AYUSH ID: This ID already exists. Please use a different one.`);
                hasDuplicateError = true;
              } else {
                // Show actual error message for other fields
                errors.push(`${key}: ${errorText}`);
              }
            } else if (typeof value === 'string') {
              const lowerValue = value.toLowerCase();
              if (key === 'ayush_id' && 
                  (lowerValue.includes('already exists') || 
                   lowerValue.includes('unique') ||
                   lowerValue.includes('duplicate'))) {
                errors.push('AYUSH ID: This ID already exists. Please use a different one.');
                hasDuplicateError = true;
              } else {
                errors.push(`${key}: ${value}`);
              }
            } else {
              errors.push(`${key}: ${JSON.stringify(value)}`);
            }
          }
          errorMessage = errors.length > 0 ? errors.join('; ') : 'Validation error occurred';
        } else if (typeof data === 'string') {
          // Check if it's HTML (Django error page)
          if (data.trim().startsWith('<!DOCTYPE') || data.trim().startsWith('<html')) {
            // Parse HTML to find actual error
            const lowerData = data.toLowerCase();
            // Only show duplicate if it's clearly an IntegrityError about unique constraint
            if (lowerData.includes('integrityerror') && 
                lowerData.includes('unique constraint') &&
                (lowerData.includes('ayush_id') || lowerData.includes('ayush'))) {
              errorMessage = 'This AYUSH ID already exists. Please use a different ID.';
            } else {
              // Generic server error
              errorMessage = 'A server error occurred. Please check your input and try again.';
            }
          } else {
            errorMessage = data;
          }
        } else {
          errorMessage = JSON.stringify(data);
        }
      } 
      // Handle 500 Internal Server Error (might be IntegrityError)
      else if (status === 500 && contentType.includes('text/html')) {
        // Check HTML content for IntegrityError
        const responseText = typeof data === 'string' ? data : '';
        if (responseText.includes('IntegrityError') && 
            (responseText.includes('UNIQUE constraint') || responseText.includes('already exists'))) {
          errorMessage = 'This AYUSH ID already exists. Please use a different ID.';
        } else {
          errorMessage = 'A server error occurred. Please try again or contact support.';
        }
      }
      // Handle network errors
      else if (!error.response) {
        errorMessage = 'Network error. Please check your connection and try again.';
      }
      // Handle other errors
      else if (error.message) {
        errorMessage = error.message;
      }
      
      setPatientError(errorMessage);
    } finally {
      setCreatingPatient(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>AYUSHAgent Dashboard</h1>
          <p>Welcome, {user?.username}</p>
        </div>
        <button onClick={logout} className="logout-button">
          Logout
        </button>
      </header>

      <div className="dashboard-content">
        <div className="dashboard-sidebar">
          <div className="sidebar-section">
            <div className="section-header">
              <h2>Patients</h2>
              <button onClick={() => setShowPatientModal(true)} className="add-button">
                + Add Patient
              </button>
            </div>
            <div className="patient-list">
              {patients.map((patient) => (
                <div
                  key={patient.id}
                  className={`patient-item ${selectedPatient?.id === patient.id ? 'active' : ''}`}
                  onClick={() => setSelectedPatient(patient)}
                >
                  <div className="patient-name">{patient.name}</div>
                  <div className="patient-id">ID: {patient.ayush_id}</div>
                </div>
              ))}
              {patients.length === 0 && (
                <p className="empty-state">No patients yet. Add one to get started.</p>
              )}
            </div>
          </div>
        </div>

        <div className="dashboard-main">
          {selectedPatient ? (
            <>
              <div className="main-section">
                <h2>Run Diagnosis Pipeline</h2>
                <div className="pipeline-form">
                  <div className="form-group">
                    <label>Patient: {selectedPatient.name} (ID: {selectedPatient.ayush_id})</label>
                  </div>
                  <div className="form-group">
                    <label htmlFor="rawText">Clinical Text / Symptoms</label>
                    <textarea
                      id="rawText"
                      value={rawText}
                      onChange={(e) => setRawText(e.target.value)}
                      placeholder="Enter patient symptoms or clinical notes..."
                      rows="6"
                    />
                  </div>
                  <div className="form-group checkbox-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={autoPush}
                        onChange={(e) => setAutoPush(e.target.checked)}
                      />
                      Auto-push to ABDM (if confidence &gt; 0.9)
                    </label>
                  </div>
                  <button
                    onClick={handleRunPipeline}
                    disabled={loading || !rawText.trim()}
                    className="run-button primary"
                  >
                    {loading ? 'Running Pipeline...' : 'Run Pipeline'}
                  </button>
                </div>
              </div>

              {(agentProgress || pipelineState) && (
                <div className="pipeline-status">
                  <h3>Agent Pipeline Status</h3>
                  
                  {agentProgress && (
                    <div className="agent-progress-container">
                      <div className="progress-steps">
                        <div className={`progress-step ${agentProgress.stage === 'extraction' || agentProgress.progress > 25 ? 'active' : ''} ${agentProgress.progress > 25 ? 'completed' : ''}`}>
                          <div className="step-icon">🔍</div>
                          <div className="step-content">
                            <div className="step-title">Extraction</div>
                            <div className="step-description">Extracting AYUSH term</div>
                          </div>
                        </div>
                        <div className={`progress-step ${agentProgress.stage === 'mapping' || agentProgress.progress > 50 ? 'active' : ''} ${agentProgress.progress > 50 ? 'completed' : ''}`}>
                          <div className="step-icon">🗺️</div>
                          <div className="step-content">
                            <div className="step-title">Mapping</div>
                            <div className="step-description">Mapping to ICD-11</div>
                          </div>
                        </div>
                        <div className={`progress-step ${agentProgress.stage === 'validation' || agentProgress.progress > 75 ? 'active' : ''} ${agentProgress.progress > 75 ? 'completed' : ''}`}>
                          <div className="step-icon">✅</div>
                          <div className="step-content">
                            <div className="step-title">Validation</div>
                            <div className="step-description">Validating confidence</div>
                          </div>
                        </div>
                        <div className={`progress-step ${agentProgress.stage === 'complete' ? 'active completed' : ''}`}>
                          <div className="step-icon">📤</div>
                          <div className="step-content">
                            <div className="step-title">Output</div>
                            <div className="step-description">Generating results</div>
                          </div>
                        </div>
                      </div>
                      <div className="progress-bar-container">
                        <div className="progress-bar" style={{ width: `${agentProgress.progress}%` }}></div>
                      </div>
                      <div className="progress-message">{agentProgress.message}</div>
                    </div>
                  )}

                  {pipelineState && (
                    <div className={`status-card ${pipelineState.stage}`}>
                      <div className="status-header">
                        <span className="status-indicator"></span>
                        <span className="status-message">{pipelineState.message}</span>
                      </div>
                      {pipelineState.error && (
                        <div className="pipeline-error">
                          <strong>Error Details:</strong>
                          <pre>{typeof pipelineState.error === 'object' ? JSON.stringify(pipelineState.error, null, 2) : pipelineState.error}</pre>
                        </div>
                      )}
                      {pipelineState.result && (
                        <div className="pipeline-result">
                          <div className="result-grid">
                            <div className="result-item">
                              <div className="result-label">AYUSH Term</div>
                              <div className="result-value">{pipelineState.result.ayush_term || 'N/A'}</div>
                            </div>
                            <div className="result-item">
                              <div className="result-label">ICD-11 Code</div>
                              <div className="result-value code">{pipelineState.result.best?.code || 'UNK'}</div>
                            </div>
                            <div className="result-item">
                              <div className="result-label">ICD-11 Title</div>
                              <div className="result-value">{pipelineState.result.best?.title || 'N/A'}</div>
                            </div>
                            <div className="result-item">
                              <div className="result-label">Confidence</div>
                              <div className="result-value confidence">
                                {((pipelineState.result.confidence || 0) * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                          {pipelineState.result.needs_human_review && (
                            <div className="result-section warning">
                              <strong>⚠️ Human Review Required</strong>
                              <p>This mapping requires manual verification before proceeding.</p>
                            </div>
                          )}
                          {pipelineState.result.reason && (
                            <div className="result-section">
                              <div className="result-label">Reason</div>
                              <div className="result-value">{pipelineState.result.reason}</div>
                            </div>
                          )}
                          {pipelineState.result.manual_review_candidates?.length > 1 && (
                            <div className="manual-review-panel">
                              <div className="result-label">Manual Review Candidates</div>
                              {pipelineState.result.review_reasons?.length ? (
                                <p className="manual-review-note">
                                  {pipelineState.result.review_reasons.join(' ')}
                                </p>
                              ) : (
                                <p className="manual-review-note">
                                  Multiple deterministic mappings detected. Please confirm the correct ICD-11 code.
                                </p>
                              )}
                              <div className="manual-review-options">
                                {pipelineState.result.manual_review_candidates.map((candidate) => (
                                  <label
                                    key={`${candidate.code}-${candidate.source_term}`}
                                    className={`manual-option ${
                                      manualSelection?.code === candidate.code ? 'active' : ''
                                    }`}
                                  >
                                    <input
                                      type="radio"
                                      name="manualCandidate"
                                      value={candidate.code}
                                      checked={manualSelection?.code === candidate.code}
                                      onChange={() => setManualSelection(candidate)}
                                    />
                                    <div>
                                      <div className="manual-option-title">{candidate.title}</div>
                                      <div className="manual-option-meta">
                                        {candidate.code} • Source term: {candidate.source_term}
                                      </div>
                                    </div>
                                  </label>
                                ))}
                              </div>
                              <div className="manual-action-row">
                                <button
                                  className="manual-apply-btn"
                                  onClick={handleManualReviewApply}
                                  disabled={!manualSelection || manualReviewStatus.saving}
                                >
                                  {manualReviewStatus.saving ? 'Saving...' : 'Apply Selection'}
                                </button>
                                <div className="manual-status">
                                  {manualReviewStatus.error && (
                                    <span className="error-text">{manualReviewStatus.error}</span>
                                  )}
                                  {manualReviewStatus.success && (
                                    <span className="success-text">{manualReviewStatus.success}</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <div className="main-section">
                <h2>Diagnosis History</h2>
                <div className="diagnosis-list">
                  {diagnoses.map((diagnosis) => (
                    <div key={diagnosis.id} className="diagnosis-card">
                      <div className="diagnosis-header">
                        <span className="diagnosis-term">{diagnosis.ayush_term}</span>
                        <span className="diagnosis-code">{diagnosis.icd_code}</span>
                      </div>
                      <div className="diagnosis-details">
                        <div>Confidence: {(diagnosis.confidence_score * 100).toFixed(1)}%</div>
                        <div className="diagnosis-date">
                          {new Date(diagnosis.created_at).toLocaleString()}
                        </div>
                      </div>
                      {diagnosis.raw_text && (
                        <div className="diagnosis-text">{diagnosis.raw_text}</div>
                      )}
                    </div>
                  ))}
                  {diagnoses.length === 0 && (
                    <p className="empty-state">No diagnoses yet. Run a pipeline to get started.</p>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state-large">
              <p>Select a patient to start diagnosing</p>
            </div>
          )}
        </div>
      </div>

      <PatientModal
        isOpen={showPatientModal}
        onClose={() => {
          setShowPatientModal(false);
          setPatientError('');
        }}
        onSubmit={handleCreatePatient}
        loading={creatingPatient}
        apiError={patientError}
      />
    </div>
  );
}

export default Dashboard;

