import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { CheckCircle2, Disc, ArrowRight, Package } from 'lucide-react';
import HankoStamp from '../components/HankoStamp';

export default function OrderSuccessPage() {
  const location = useLocation();
  const orderData = location.state?.order;
  const items = location.state?.items || [];
  const total = location.state?.total || 0;

  const orderId = orderData?.id || 'OT-' + Math.random().toString(36).substring(2, 9).toUpperCase();

  return (
    <div style={{ backgroundColor: 'var(--bg)', minHeight: '85vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 24px' }}>
      <div style={{
        maxWidth: '580px',
        width: '100%',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--taupe-border)',
        borderRadius: 'var(--radius-lg)',
        padding: '48px 36px',
        textAlign: 'center',
        boxShadow: '0 16px 40px rgba(0,0,0,0.6)'
      }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          backgroundColor: 'rgba(200, 155, 60, 0.15)',
          border: '1px solid var(--brass)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          color: 'var(--brass)'
        }}>
          <CheckCircle2 size={32} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: 'var(--ink)' }}>
            Order Confirmed
          </h1>
          <HankoStamp text="受" size={22} rotation={-2} />
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '28px', lineHeight: '1.6' }}>
          Thank you for ordering from Otoichi. Your pressing has been logged and queued for inspection and rigid mailer packaging.
        </p>

        {/* Order Details Badge Box */}
        <div style={{
          backgroundColor: 'var(--taupe-dark)',
          border: '1px solid var(--taupe-border)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          textAlign: 'left',
          marginBottom: '32px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.85rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ color: 'var(--text-muted)' }}>ORDER NUMBER:</span>
            <span style={{ color: 'var(--brass)', fontWeight: 600 }}>{orderId}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ color: 'var(--text-muted)' }}>STATUS:</span>
            <span style={{ color: '#79D49B' }}>PAID & PROCESSING</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>ESTIMATED DISPATCH:</span>
            <span style={{ color: 'var(--ink)' }}>Within 24 Hours</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
          <Link to="/browse" className="btn-brass">
            <span>Explore More Pressings</span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    </div>
  );
}
