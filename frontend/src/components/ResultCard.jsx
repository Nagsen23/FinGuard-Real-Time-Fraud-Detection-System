import React from 'react';
import RiskBadge from './RiskBadge';
import ReasonsList from './ReasonsList';

const ResultCard = ({ result }) => {
  if (!result) return null;

  const { fraud_probability, risk_level, decision, top_reasons, _timestamp } = result;
  
  const getColors = (desc) => {
    switch (desc?.toUpperCase()) {
      case 'ALLOW': return { bg: '#ecfdf5', text: '#059669', border: '#34d399', glowing: false };
      case 'REVIEW': return { bg: '#fffbeb', text: '#d97706', border: '#fbbf24', glowing: false };
      case 'BLOCK': return { bg: '#fef2f2', text: '#dc2626', border: '#ef4444', glowing: true };
      default: return { bg: '#f8fafc', text: '#64748b', border: '#cbd5e1', glowing: false };
    }
  };

  const scheme = getColors(decision);
  const probPercentage = (fraud_probability * 100).toFixed(1);
  const probColor = fraud_probability > 0.7 ? '#dc2626' : fraud_probability > 0.3 ? '#f59e0b' : '#059669';

  return (
    <div key={_timestamp} className={`card slide-up ${scheme.glowing ? 'glowing' : ''}`} style={{ 
      padding: '2.5rem', 
      borderTop: `4px solid ${scheme.border}`,
      animation: scheme.glowing ? 'slideUp 0.5s ease-out, pulse-glow 2s infinite' : 'slideUp 0.5s ease-out'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--navy)', fontSize: '1.25rem', fontWeight: '700' }}>Evaluation Result</h3>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Automated decision engine output</p>
        </div>
        <RiskBadge level={risk_level} size="lg" />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', backgroundColor: '#f8fafc', borderRadius: '12px', padding: '1.5rem', marginBottom: '2rem', border: '1px solid var(--border)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
            Action Required
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: scheme.text, letterSpacing: '-0.025em' }}>
            {decision || 'UNKNOWN'}
          </div>
        </div>
        <div style={{ height: '60px', width: '1px', backgroundColor: 'var(--border)', margin: '0 2rem' }}></div>
        <div style={{ flex: 1, textAlign: 'right' }}>
          <div style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
            Fraud Confidence
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: probColor, letterSpacing: '-0.025em' }}>
            {probPercentage}%
          </div>
        </div>
      </div>

      <ReasonsList reasons={top_reasons} />
    </div>
  );
};

export default ResultCard;
