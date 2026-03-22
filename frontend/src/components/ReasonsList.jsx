import React from 'react';

const formatLabel = (key) => {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const ReasonsList = ({ reasons }) => {
  if (!reasons || reasons.length === 0) return null;

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h4 style={{ margin: '0 0 1rem 0', fontSize: '0.875rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Key Risk Factors
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {reasons.map((reason, idx) => {
          const percentage = Math.round(reason.contribution * 100);
          const barColor = percentage > 40 ? '#ef4444' : percentage > 20 ? '#f59e0b' : '#3b82f6';
          
          return (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                <span style={{ fontWeight: '500', color: '#1e293b' }}>{formatLabel(reason.feature)}</span>
                <span style={{ color: '#64748b', fontWeight: '600' }}>{percentage}%</span>
              </div>
              <div style={{ height: '6px', backgroundColor: '#e2e8f0', borderRadius: '99px', overflow: 'hidden' }}>
                <div 
                  style={{ 
                    height: '100%', 
                    width: `${percentage}%`, 
                    backgroundColor: barColor,
                    borderRadius: '99px',
                    transition: 'width 1s cubic-bezier(0.16, 1, 0.3, 1)'
                  }} 
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ReasonsList;
