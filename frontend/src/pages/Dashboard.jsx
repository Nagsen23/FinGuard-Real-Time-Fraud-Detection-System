import React, { useState } from 'react';
import TransactionForm from '../components/TransactionForm';
import ResultCard from '../components/ResultCard';
import AuditTable from '../components/AuditTable';

const StatCard = ({ title, value, color, icon, delay }) => (
  <div className={`card fade-in ${delay}`} style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem', borderTop: `4px solid ${color}` }}>
    <div style={{ width: '50px', height: '50px', borderRadius: '12px', backgroundColor: `${color}15`, color: color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {icon}
    </div>
    <div>
      <p style={{ margin: '0 0 0.25rem 0', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</p>
      <h4 style={{ margin: 0, color: 'var(--navy)', fontSize: '1.75rem', fontWeight: '800', letterSpacing: '-0.025em' }}>{value !== null ? value : '-'}</h4>
    </div>
  </div>
);

const Dashboard = () => {
  const [currentResult, setCurrentResult] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [stats, setStats] = useState({ total: null, allowed: null, review: null, blocked: null });

  const handleResult = (result) => {
    setCurrentResult(result);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleStart = () => {
    // Optional: we can clear the result or keep it showing while loading.
    // setCurrentResult(null); 
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '2rem 1.5rem', minHeight: '100vh' }}>
      <header className="fade-in" style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--blue) 0%, #1d4ed8 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '1.2rem' }}>
              F
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--navy)', margin: 0, letterSpacing: '-0.025em' }}>
              FinGuard
            </h1>
          </div>
          <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '0.95rem' }}>
            Real-Time Fraud Prevention & Intelligence
          </p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>System Status</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--green)', fontSize: '0.8rem', fontWeight: '500' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--green)', boxShadow: '0 0 8px var(--green)' }}></span>
              All Systems Operational
            </div>
          </div>
        </div>
      </header>
      
      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <StatCard 
          title="Recent Transactions" 
          value={stats.total} 
          color="var(--blue)" 
          delay=""
          icon={<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '24px', height: '24px' }}><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
        />
        <StatCard 
          title="Allowed (Safe)" 
          value={stats.allowed} 
          color="var(--green)" 
          delay="delay-100"
          icon={<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '24px', height: '24px' }}><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <StatCard 
          title="Manual Review" 
          value={stats.review} 
          color="var(--amber)" 
          delay="delay-200"
          icon={<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '24px', height: '24px' }}><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
        />
        <StatCard 
          title="Blocked (Fraud)" 
          value={stats.blocked} 
          color="var(--red)" 
          delay="delay-200"
          icon={<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '24px', height: '24px' }}><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr', gap: '2.5rem', alignItems: 'start' }}>
        {/* Left Column */}
        <div>
          <TransactionForm onStart={handleStart} onResult={handleResult} />
          <ResultCard result={currentResult} />
        </div>
        
        {/* Right Column */}
        <div style={{ position: 'sticky', top: '2rem' }}>
          <AuditTable refreshTrigger={refreshTrigger} onStatsExtracted={setStats} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
