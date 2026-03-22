import React, { useEffect, useState } from 'react';
import api from '../api/client';
import RiskBadge from './RiskBadge';

const AuditTable = ({ refreshTrigger, onStatsExtracted }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAuditLogs();
  }, [refreshTrigger]);

  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/audit/recent?limit=15');
      const data = Array.isArray(res.data) ? res.data : [];
      setLogs(data);
      setError(null);
      
      // Extract stats for the dashboard if callback exists
      if (onStatsExtracted && data.length > 0) {
        const stats = {
          total: data.length,
          allowed: data.filter(l => l.decision === 'ALLOW').length,
          review: data.filter(l => l.decision === 'REVIEW').length,
          blocked: data.filter(l => l.decision === 'BLOCK').length
        };
        onStatsExtracted(stats);
      }
    } catch (err) {
      console.error('Audit fetch error:', err);
      setError('Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  const getDecisionStyle = (decision) => {
    switch(decision) {
      case 'BLOCK': return { color: '#dc2626', bg: '#fef2f2' };
      case 'ALLOW': return { color: '#059669', bg: '#ecfdf5' };
      case 'REVIEW': return { color: '#d97706', bg: '#fffbeb' };
      default: return { color: '#475569', bg: '#f1f5f9' };
    }
  };

  if (loading && logs.length === 0) {
    return (
      <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <svg className="animate-spin" style={{ width: '30px', height: '30px', margin: '0 auto 1rem', color: 'var(--blue)', animation: 'spin 1s linear infinite' }} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.25"></circle>
          <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Loading recent transactions...
      </div>
    );
  }

  if (error) {
    return <div className="card fade-in" style={{ padding: '2rem', color: '#dc2626', backgroundColor: '#fef2f2', borderLeft: '4px solid #ef4444' }}>{error}</div>;
  }

  return (
    <div className="card fade-in delay-200" style={{ overflow: 'hidden' }}>
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border)', backgroundColor: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0, color: 'var(--navy)', fontSize: '1.1rem', fontWeight: '700' }}>Recent Activity</h3>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Latest automated scoring logs</p>
        </div>
        <button onClick={fetchAuditLogs} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: '6px', padding: '0.5rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '16px', height: '16px' }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ backgroundColor: '#ffffff', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Time</th>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Transaction ID</th>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Risk Level</th>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Decision</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No recent transactions found.
                </td>
              </tr>
            ) : (
              logs.map((log) => {
                const style = getDecisionStyle(log.decision);
                return (
                  <tr key={log.id || `${log.transaction_id}-${log.created_at}`} style={{ borderBottom: '1px solid var(--border)', transition: 'background-color 0.2s ease' }} onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'} onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                    <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                      {log.created_at ? new Date(log.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '-'}
                    </td>
                    <td style={{ padding: '1rem 1.5rem', color: 'var(--navy)', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace', fontSize: '0.8rem' }}>
                      {log.transaction_id}
                    </td>
                    <td style={{ padding: '1rem 1.5rem' }}>
                      <RiskBadge level={log.risk_level} />
                    </td>
                    <td style={{ padding: '1rem 1.5rem' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', padding: '0.25rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: '700', letterSpacing: '0.05em', color: style.color, backgroundColor: style.bg }}>
                        {log.decision}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditTable;