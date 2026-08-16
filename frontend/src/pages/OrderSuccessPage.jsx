import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { CheckCircle2, Disc, ArrowRight, Package, ShieldCheck, Clock } from 'lucide-react';
import HankoStamp from '../components/HankoStamp';
import { getProductDisplay } from '../utils/productHelper';

export default function OrderSuccessPage() {
  const location = useLocation();
  const orderData = location.state?.order;
  const items = location.state?.items || orderData?.items || [];
  const total = location.state?.total || orderData?.total_amount || 0;

  const orderId = orderData?.id ? String(orderData.id) : (orderData?.checkout_id || 'OT-ORD-CONFIRMED');
  const isProcessing = orderData?.payment_status === 'processing';
  const isPaid = orderData?.status === 'paid' || orderData?.payment_status === 'succeeded';

  const shippingSnapshot = orderData?.shipping_address_snapshot || {};

  return (
    <div style={{ backgroundColor: 'var(--bg)', minHeight: '85vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 24px' }}>
      <div style={{
        maxWidth: '640px',
        width: '100%',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--taupe-border)',
        borderRadius: 'var(--radius-lg)',
        padding: '48px 36px',
        textAlign: 'center',
        boxShadow: '0 16px 40px rgba(0,0,0,0.6)'
      }}>
        {/* Status Icon */}
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          backgroundColor: isPaid ? 'rgba(200, 155, 60, 0.15)' : 'rgba(200, 155, 60, 0.1)',
          border: isPaid ? '1px solid var(--brass)' : '1px solid var(--taupe-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          color: isPaid ? 'var(--brass)' : '#C89B3C'
        }}>
          {isProcessing ? <Clock size={32} /> : <CheckCircle2 size={32} />}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: 'var(--ink)' }}>
            {isProcessing ? 'Payment Processing' : 'Order Confirmed'}
          </h1>
          <HankoStamp text="受" size={22} rotation={-2} />
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '28px', lineHeight: '1.6' }}>
          {isProcessing
            ? 'Your payment is currently settling with Stripe. Your order is secured and we will notify you once confirmation finishes.'
            : 'Thank you for ordering from Otoichi. Your pressing has been logged and queued for inspection and rigid mailer packaging.'}
        </p>

        {/* Order Details Badge Box */}
        <div style={{
          backgroundColor: 'var(--taupe-dark)',
          border: '1px solid var(--taupe-border)',
          borderRadius: 'var(--radius-md)',
          padding: '24px',
          textAlign: 'left',
          marginBottom: '32px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.85rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', borderBottom: '1px solid rgba(243, 236, 221, 0.08)', paddingBottom: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>ORDER REFERENCE:</span>
            <span style={{ color: 'var(--brass)', fontWeight: 600 }}>{orderId}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)' }}>PAYMENT STATUS:</span>
            <span style={{ color: isPaid ? '#79D49B' : '#C89B3C', fontWeight: 600 }}>
              {isPaid ? 'PAID & CONFIRMED' : 'PROCESSING WITH STRIPE'}
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)' }}>TOTAL PAID:</span>
            <span style={{ color: 'var(--ink)', fontWeight: 600 }}>${Number(total).toFixed(2)}</span>
          </div>

          {shippingSnapshot.city && (
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>DESTINATION:</span>
              <span style={{ color: 'var(--ink-secondary)' }}>
                {shippingSnapshot.city}, {shippingSnapshot.country || 'US'}
              </span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>ESTIMATED DISPATCH:</span>
            <span style={{ color: 'var(--ink)' }}>Dispatched in rigid mailer within 24h</span>
          </div>
        </div>

        {/* Action Button */}
        <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
          <Link to="/browse" className="btn-brass" style={{ padding: '12px 28px' }}>
            <span>Explore More Pressings</span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    </div>
  );
}
