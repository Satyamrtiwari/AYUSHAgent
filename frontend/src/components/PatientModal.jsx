import { useState } from 'react';
import './PatientModal.css';

const PatientModal = ({ isOpen, onClose, onSubmit, loading, apiError }) => {
  const [formData, setFormData] = useState({ name: '', ayush_id: '', age: '' });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    let value = e.target.value;
    
    // Auto-format AYUSH ID: "AY" + exactly 5 digits
    if (e.target.name === 'ayush_id') {
      // Remove any non-alphanumeric characters
      value = value.toUpperCase().replace(/[^A-Z0-9]/g, '');
      
      // Ensure it starts with "AY"
      if (value && !value.startsWith('AY')) {
        if (value.startsWith('A')) {
          value = 'AY' + value.substring(1);
        } else {
          value = 'AY' + value;
        }
      }
      
      // Limit to "AY" + 5 digits maximum
      if (value.length > 7) {
        value = value.substring(0, 7);
      }
      
      // Only allow digits after "AY"
      if (value.length > 2) {
        const prefix = value.substring(0, 2);
        const digits = value.substring(2).replace(/\D/g, '');
        value = prefix + digits;
      }
    }
    
    setFormData({
      ...formData,
      [e.target.name]: value,
    });
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!formData.name.trim()) {
      setError('Patient name is required');
      return;
    }

    if (!formData.ayush_id.trim()) {
      setError('AYUSH ID is required');
      return;
    }

    // Validate AYUSH ID format: AY + exactly 5 digits
    const ayushIdPattern = /^AY\d{5}$/;
    if (!ayushIdPattern.test(formData.ayush_id)) {
      setError('AYUSH ID must be in format: AY followed by exactly 5 digits (e.g., AY00001)');
      return;
    }

    const age = parseInt(formData.age);
    if (!formData.age.trim() || isNaN(age) || age < 0 || age > 150) {
      setError('Please enter a valid age (0-150)');
      return;
    }

    onSubmit({ ...formData, age });
  };

  const handleClose = () => {
    setFormData({ name: '', ayush_id: '', age: '' });
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add New Patient</h2>
          <button className="modal-close" onClick={handleClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {(error || apiError) && <div className="modal-error">{error || apiError}</div>}

          <div className="form-group">
            <label htmlFor="name">Patient Name *</label>
            <input
              id="name"
              name="name"
              type="text"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter patient full name"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="ayush_id">AYUSH ID *</label>
            <input
              id="ayush_id"
              name="ayush_id"
              type="text"
              value={formData.ayush_id}
              onChange={handleChange}
              placeholder="AY00001"
              maxLength={7}
              required
              disabled={loading}
            />
            <small className="input-hint">Format: AY followed by 5 digits (e.g., AY00001)</small>
          </div>

          <div className="form-group">
            <label htmlFor="age">Age *</label>
            <input
              id="age"
              name="age"
              type="number"
              min="0"
              max="150"
              value={formData.age}
              onChange={handleChange}
              placeholder="Enter patient age"
              required
              disabled={loading}
            />
          </div>

          <div className="modal-actions">
            <button type="button" onClick={handleClose} className="modal-button cancel" disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="modal-button primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PatientModal;

