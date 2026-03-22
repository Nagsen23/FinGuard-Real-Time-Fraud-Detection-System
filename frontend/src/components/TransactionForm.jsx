import React, { useState } from 'react';
import api from '../api/client';

const initialForm = {
  transaction_id: `tx_${Date.now()}`,
  user_id: 'user_123',
  merchant_id: 'merchant_456',
  amount: 500.0,
  transaction_type: 'purchase',
  merchant_category: 'retail',
  device_type: 'mobile',
  channel: 'online',
  city: 'New York',
  country: 'US',
  timestamp: new Date().toISOString(),
  is_international: false,
  card_present: false
};

const TransactionForm = ({ onResult, onStart }) => {
  const [formData, setFormData] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    onStart();
    try {
      const payload = {
        transaction_id: formData.transaction_id || `tx_${Date.now()}`,
        user_id: formData.user_id,
        merchant_id: formData.merchant_id,
        amount: Number(formData.amount),
        transaction_type: formData.transaction_type,
        merchant_category: formData.merchant_category,
        device_type: formData.device_type,
        channel: formData.channel,
        city: formData.city,
        country: formData.country,
        timestamp: new Date().toISOString(),
        is_international: Boolean(formData.is_international),
        card_present: Boolean(formData.card_present)
      };
      const res = await api.post('/predict', payload);
      onResult({...res.data, _timestamp: Date.now()}); // Ensure new reference triggers animation
    } catch (err) {
      console.error('Prediction fetch error:', err);
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map(e => JSON.stringify(e)).join(', ') : (detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card fade-in" style={{ padding: '2rem', marginBottom: '1.5rem', borderTop: '4px solid var(--blue)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--blue)' }}>
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '24px', height: '24px' }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h3 style={{ margin: 0, color: 'var(--navy)', fontSize: '1.25rem', fontWeight: '700' }}>Submit Transaction</h3>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Real-time fraud scoring API</p>
        </div>
      </div>
      
      {error && (
        <div className="slide-up" style={{ padding: '1rem', backgroundColor: '#fef2f2', borderLeft: '4px solid var(--red)', color: '#991b1b', borderRadius: '4px', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          <strong>Error: </strong>{error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(200px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
          <div>
            <label className="input-label">Amount ($)</label>
            <input type="number" name="amount" value={formData.amount} onChange={handleChange} step="0.01" className="input-field" required />
          </div>
          <div>
            <label className="input-label">User ID</label>
            <input type="text" name="user_id" value={formData.user_id} onChange={handleChange} className="input-field" required />
          </div>
          <div>
            <label className="input-label">Merchant ID</label>
            <input type="text" name="merchant_id" value={formData.merchant_id} onChange={handleChange} className="input-field" required />
          </div>
          <div>
            <label className="input-label">Category</label>
            <select name="merchant_category" value={formData.merchant_category} onChange={handleChange} className="input-field">
              <option value="retail">Retail</option>
              <option value="travel">Travel</option>
              <option value="food">Food</option>
              <option value="entertainment">Entertainment</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="input-label">Type</label>
            <select name="transaction_type" value={formData.transaction_type} onChange={handleChange} className="input-field">
              <option value="purchase">Purchase</option>
              <option value="transfer">Transfer</option>
              <option value="withdrawal">Withdrawal</option>
            </select>
          </div>
          <div>
            <label className="input-label">Country (ISO)</label>
            <input type="text" name="country" value={formData.country} onChange={handleChange} maxLength={2} className="input-field" required />
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '2rem', padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid var(--border)' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: 'var(--navy)', cursor: 'pointer', fontWeight: '500' }}>
            <input type="checkbox" name="is_international" checked={formData.is_international} onChange={handleChange} style={{ width: '16px', height: '16px', accentColor: 'var(--blue)' }} />
            International Transaction
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: 'var(--navy)', cursor: 'pointer', fontWeight: '500' }}>
            <input type="checkbox" name="card_present" checked={formData.card_present} onChange={handleChange} style={{ width: '16px', height: '16px', accentColor: 'var(--blue)' }} />
            Card Present
          </label>
        </div>

        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? (
            <>
              <svg className="animate-spin" style={{ width: '20px', height: '20px', animation: 'spin 1s linear infinite' }} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.25"></circle>
                <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing...
            </>
          ) : (
             <>
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '20px', height: '20px' }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Score Transaction
             </>
          )}
        </button>
      </form>
      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    </div>
  );
};

export default TransactionForm;
