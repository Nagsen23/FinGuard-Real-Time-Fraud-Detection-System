import React from 'react';

const RiskBadge = ({ level, size = 'md' }) => {
  const isLarge = size === 'lg';
  
  const getBadgeStyle = () => {
    switch (level?.toLowerCase()) {
      case 'low':
        return { 
          backgroundColor: '#ecfdf5', 
          color: '#059669', 
          border: '1px solid #10b981' 
        };
      case 'medium':
        return { 
          backgroundColor: '#fffbeb', 
          color: '#d97706', 
          border: '1px solid #f59e0b' 
        };
      case 'high':
      case 'critical':
        return { 
          backgroundColor: '#fef2f2', 
          color: '#dc2626', 
          border: '1px solid #ef4444',
        };
      default:
        return { 
          backgroundColor: '#f8fafc', 
          color: '#64748b', 
          border: '1px solid #cbd5e1' 
        };
    }
  };

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.35rem',
      padding: isLarge ? '6px 14px' : '4px 10px',
      borderRadius: '9999px',
      fontSize: isLarge ? '0.95rem' : '0.8rem',
      fontWeight: '600',
      letterSpacing: '0.025em',
      textTransform: 'uppercase',
      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
      ...getBadgeStyle()
    }}>
      {level === 'critical' || level === 'high' ? (
        <svg fill="currentColor" viewBox="0 0 20 20" style={{ width: isLarge ? '1rem' : '0.875rem', height: isLarge ? '1rem' : '0.875rem' }}>
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      ) : (
        <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'currentColor' }} />
      )}
      {level || 'UNKNOWN'}
    </span>
  );
};

export default RiskBadge;
