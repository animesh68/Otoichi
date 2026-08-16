import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Lock, ShieldCheck, CreditCard } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { CheckoutService } from '../api/services';
import { getProductDisplay } from '../utils/productHelper';
import confetti from 'canvas-confetti';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { cart, coupon, clearCart } = useCart();
  const { user, login, register, isAuthenticated } = useAuth();

  const [isAuthMode, setIsAuthMode] = useState(false);
  const [authType, setAuthType] = useState('login');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authName, setAuthName] = useState('');
  const [authError, setAuthError] = useState(null);

  const [formData, setFormData] = useState({
    email: user?.email || '',
    full_name: user?.full_name || '',
    street: '12-4 Shibuya Dogenzaka',
    city: 'Tokyo',
    state: 'Tokyo',
    postal_code: '150-0043',
    country: 'Japan',
    card_number: '4242 •••• •••• 4242',
    card_exp: '12/28',
    card_cvc: '888'
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const items = cart?.items || [];
  const subtotal = items.reduce((sum, item) => {
    const d = getProductDisplay(item);
    return sum + (d.price * (item.quantity || 1));
  }, 0);

  let discountAmount = 0;
  if (coupon) {
    if (coupon.discount_percent) {
      discountAmount = (subtotal * coupon.discount_percent) / 100;
    } else if (coupon.discount_amount) {
      discountAmount = coupon.discount_amount;
    }
  }

  const shipping = subtotal > 100 || subtotal === 0 ? 0 : 7.50;
  const total = Math.max(0, subtotal - discountAmount + shipping);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError(null);
    try {
      if (authType === 'login') {
        await login(authEmail, authPassword);
      } else {
        await register({ email: authEmail, password: authPassword, full_name: authName });
      }
      setIsAuthMode(false);
      setFormData(prev => ({ ...prev, email: authEmail, full_name: authName || prev.full_name }));
    } catch (err) {
      setAuthError(err.message || 'Authentication failed');
    }
  };

  const handlePlaceOrder = async (e) => {
    e.preventDefault();
    if (items.length === 0) {
      navigate('/browse');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const orderPayload = {
        email: formData.email || user?.email || 'guest@otoichi.com',
        shipping_address: {
          full_name: formData.full_name || 'Collector',
          street: formData.street,
          city: formData.city,
          state: formData.state,
          postal_code: formData.postal_code,
          country: formData.country
        },
        coupon_code: coupon?.code || null
      };

      const res = await CheckoutService.directOrder(orderPayload);
      
      try {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#C89B3C', '#F3ECDD', '#8C2F2F']
        });
      } catch (e) {}

      await clearCart();
      navigate('/order-success', { state: { order: res, items, total } });
    } catch (err) {
      console.error('Order checkout error:', err);
      setErrorMsg(err.message || 'Checkout failed. Please check stock and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ backgroundColor: 'var(--bg)', minHeight: '100vh', padding: '40px 0 100px' }}>
      <div className="container">
        
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--taupe-border)',
          paddingBottom: '20px',
          marginBottom: '40px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.2rem', color: 'var(--ink)', fontWeight: 400 }}>
              Checkout
            </h1>
            <span style={{ fontFamily: 'var(--font-script)', color: 'var(--brass)', fontSize: '1.4rem' }}>
              決済
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#79D49B', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
            <ShieldCheck size={16} />
            <span>Secure 256-Bit SSL</span>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '48px',
          alignItems: 'start'
        }}>
          
          {/* Left Column: Shipping & Payment Form */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            
            {/* Account / Guest Section */}
            <div style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--taupe-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '24px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.15rem', color: 'var(--ink)' }}>
                  1. Contact Information
                </h3>
                {!isAuthenticated && (
                  <button
                    onClick={() => setIsAuthMode(!isAuthMode)}
                    style={{ color: 'var(--brass)', fontSize: '0.82rem', textDecoration: 'underline' }}
                  >
                    {isAuthMode ? 'Continue as Guest' : 'Sign in / Create Account'}
                  </button>
                )}
              </div>

              {isAuthMode && !isAuthenticated ? (
                <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {authType === 'register' && (
                    <input
                      type="text"
                      placeholder="Full Name"
                      required
                      value={authName}
                      onChange={e => setAuthName(e.target.value)}
                      style={{
                        padding: '10px 14px',
                        backgroundColor: 'var(--taupe)',
                        border: '1px solid var(--taupe-border)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--ink)',
                        fontSize: '0.9rem'
                      }}
                    />
                  )}
                  <input
                    type="email"
                    placeholder="Email Address"
                    required
                    value={authEmail}
                    onChange={e => setAuthEmail(e.target.value)}
                    style={{
                      padding: '10px 14px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontSize: '0.9rem'
                    }}
                  />
                  <input
                    type="password"
                    placeholder="Password"
                    required
                    value={authPassword}
                    onChange={e => setAuthPassword(e.target.value)}
                    style={{
                      padding: '10px 14px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontSize: '0.9rem'
                    }}
                  />
                  {authError && <div style={{ color: '#F38A8A', fontSize: '0.8rem' }}>{authError}</div>}
                  <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                    <button type="submit" className="btn-brass" style={{ padding: '8px 18px', fontSize: '0.85rem' }}>
                      {authType === 'login' ? 'Sign In' : 'Create Account'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setAuthType(authType === 'login' ? 'register' : 'login')}
                      style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}
                    >
                      {authType === 'login' ? 'Need an account? Register' : 'Already have an account? Sign in'}
                    </button>
                  </div>
                </form>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <input
                    type="email"
                    name="email"
                    placeholder="Recipient Email (for tracking & receipt)"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    style={{
                      padding: '12px 16px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
              )}
            </div>

            {/* Shipping Address Section */}
            <div style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--taupe-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '24px'
            }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.15rem', color: 'var(--ink)', marginBottom: '16px' }}>
                2. Shipping Address (Rigid Mailer Courier)
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div style={{ gridColumn: 'span 2' }}>
                  <input
                    type="text"
                    name="full_name"
                    placeholder="Full Name"
                    required
                    value={formData.full_name}
                    onChange={handleInputChange}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>

                <div style={{ gridColumn: 'span 2' }}>
                  <input
                    type="text"
                    name="street"
                    placeholder="Street Address"
                    required
                    value={formData.street}
                    onChange={handleInputChange}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>

                <div>
                  <input
                    type="text"
                    name="city"
                    placeholder="City"
                    required
                    value={formData.city}
                    onChange={handleInputChange}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>

                <div>
                  <input
                    type="text"
                    name="postal_code"
                    placeholder="Postal Code"
                    required
                    value={formData.postal_code}
                    onChange={handleInputChange}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Payment Details Section */}
            <div style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--taupe-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '24px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.15rem', color: 'var(--ink)' }}>
                  3. Payment Method
                </h3>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--brass)' }}>
                  Stripe Test Mode Enabled
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  backgroundColor: 'var(--taupe)',
                  border: '1px solid var(--taupe-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 16px'
                }}>
                  <CreditCard size={18} color="var(--brass)" style={{ marginRight: '12px' }} />
                  <input
                    type="text"
                    name="card_number"
                    value={formData.card_number}
                    onChange={handleInputChange}
                    style={{ background: 'none', border: 'none', color: 'var(--ink)', fontFamily: 'var(--font-mono)', width: '100%' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <input
                    type="text"
                    name="card_exp"
                    value={formData.card_exp}
                    onChange={handleInputChange}
                    style={{
                      padding: '12px 16px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontFamily: 'var(--font-mono)'
                    }}
                  />
                  <input
                    type="text"
                    name="card_cvc"
                    value={formData.card_cvc}
                    onChange={handleInputChange}
                    style={{
                      padding: '12px 16px',
                      backgroundColor: 'var(--taupe)',
                      border: '1px solid var(--taupe-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--ink)',
                      fontFamily: 'var(--font-mono)'
                    }}
                  />
                </div>
              </div>
            </div>

            {errorMsg && (
              <div style={{
                backgroundColor: 'rgba(140, 47, 47, 0.15)',
                border: '1px solid var(--seal)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                color: '#F38A8A',
                fontSize: '0.85rem'
              }}>
                {errorMsg}
              </div>
            )}

            {/* Place Order CTA */}
            <button
              onClick={handlePlaceOrder}
              disabled={isSubmitting}
              className="btn-brass"
              style={{ width: '100%', padding: '16px', fontSize: '1.05rem' }}
            >
              <Lock size={18} />
              <span>{isSubmitting ? 'Processing Order...' : `Authorize & Pay $${total.toFixed(2)}`}</span>
            </button>
          </div>

          {/* Right Column: Order Summary */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--taupe-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '28px',
            position: 'sticky',
            top: '90px'
          }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', color: 'var(--ink)', marginBottom: '16px' }}>
              Items in Shipment ({items.length})
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '280px', overflowY: 'auto', marginBottom: '20px' }}>
              {items.map((item) => {
                const d = getProductDisplay(item);
                const qty = item.quantity || 1;
                return (
                  <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <img
                      src={d.coverArt}
                      alt={d.title}
                      style={{ width: '42px', height: '42px', borderRadius: '4px', objectFit: 'cover' }}
                    />
                    <div style={{ flexGrow: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.85rem', color: 'var(--ink)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {d.title}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        Qty: {qty} • ${(d.price * qty).toFixed(2)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ borderTop: '1px solid var(--taupe-border)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink-secondary)' }}>
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              {discountAmount > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--brass)' }}>
                  <span>Discount</span>
                  <span>-${discountAmount.toFixed(2)}</span>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink-secondary)' }}>
                <span>Shipping</span>
                <span>{shipping === 0 ? 'FREE' : `$${shipping.toFixed(2)}`}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink)', fontSize: '1.15rem', fontWeight: 600, borderTop: '1px solid var(--taupe-border)', paddingTop: '12px' }}>
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
