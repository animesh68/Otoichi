import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Elements } from '@stripe/react-stripe-js';
import { Lock, ShieldCheck, Tag, Disc, AlertCircle, ArrowLeft } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { CheckoutService } from '../api/services';
import { stripePromise } from '../api/stripeClient';
import StripeCheckoutForm from '../components/StripeCheckoutForm';
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
    street: '742 Evergreen Terrace',
    city: 'Springfield',
    state: 'OR',
    postal_code: '97477',
    country: 'United States',
  });

  const [summary, setSummary] = useState(null);
  const [clientSecret, setClientSecret] = useState(null);
  const [paymentIntentId, setPaymentIntentId] = useState(null);
  const [checkoutId, setCheckoutId] = useState(null);
  const [isZeroTotal, setIsZeroTotal] = useState(false);
  const [isMockMode, setIsMockMode] = useState(false);
  const [loadingIntent, setLoadingIntent] = useState(true);
  const [initError, setInitError] = useState(null);

  const items = cart?.items || [];

  // Fetch authoritative pricing breakdown and create PaymentIntent
  useEffect(() => {
    async function initCheckout() {
      if (items.length === 0) {
        setLoadingIntent(false);
        return;
      }

      setLoadingIntent(true);
      setInitError(null);

      try {
        const intentRes = await CheckoutService.createIntent({
          coupon_code: coupon?.code || undefined,
          guest_email: formData.email || undefined,
        });

        setSummary({
          subtotal: intentRes.subtotal,
          shipping: intentRes.shipping,
          discount: intentRes.discount,
          total: intentRes.total,
          currency: intentRes.currency,
        });
        setCheckoutId(intentRes.checkout_id);
        setIsZeroTotal(intentRes.is_zero_total);

        if (intentRes.is_zero_total) {
          setClientSecret(null);
          setPaymentIntentId(null);
        } else {
          setClientSecret(intentRes.client_secret);
          setPaymentIntentId(intentRes.payment_intent_id);
          if (!intentRes.client_secret || intentRes.client_secret.includes('secret_mock')) {
            setIsMockMode(true);
          }
        }
      } catch (err) {
        console.error('Error initializing checkout payment:', err);
        setInitError(err.message || 'Could not calculate checkout totals. Please verify stock.');
      } finally {
        setLoadingIntent(false);
      }
    }

    initCheckout();
  }, [coupon, items.length]);

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

  const handleZeroTotalCheckout = async () => {
    try {
      setLoadingIntent(true);
      const order = await CheckoutService.createZeroTotalOrder({
        coupon_code: coupon?.code || '',
        new_shipping_address: {
          line1: formData.street,
          city: formData.city,
          state: formData.state,
          postal_code: formData.postal_code,
          country: formData.country,
          phone: '',
        }
      });

      try {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#C89B3C', '#F3ECDD', '#8C2F2F']
        });
      } catch (e) {}

      await clearCart();
      navigate('/order-success', {
        state: {
          order: order,
          items: items,
          total: 0.0
        }
      });
    } catch (err) {
      setInitError(err.message || 'Zero-total checkout failed');
    } finally {
      setLoadingIntent(false);
    }
  };

  // Stripe theme customization matching Otoichi dark/brass palette
  const stripeAppearance = {
    theme: 'night',
    variables: {
      colorPrimary: '#C89B3C',
      colorBackground: '#1C1814',
      colorText: '#F3ECDD',
      colorDanger: '#F38A8A',
      fontFamily: 'Instrument Sans, sans-serif',
      spacingUnit: '4px',
      borderRadius: '6px',
    },
    rules: {
      '.Input': {
        backgroundColor: '#2A241E',
        border: '1px solid #3A342C',
        color: '#F3ECDD',
        boxShadow: 'none',
      },
      '.Input:focus': {
        borderColor: '#C89B3C',
        boxShadow: '0 0 0 1px #C89B3C',
      },
      '.Label': {
        color: '#A89E90',
        fontSize: '0.8rem',
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
      },
      '.Tab': {
        backgroundColor: '#2A241E',
        borderColor: '#3A342C',
        color: '#A89E90',
      },
      '.Tab--selected': {
        borderColor: '#C89B3C',
        color: '#F3ECDD',
        backgroundColor: '#1C1814',
      }
    }
  };

  if (items.length === 0) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '100px 24px', minHeight: '60vh' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: 'var(--ink)', marginBottom: '16px' }}>
          Your Crate is Empty
        </h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
          Add vinyl pressings to your crate before checking out.
        </p>
        <Link to="/browse" className="btn-brass">
          Browse Record Crates
        </Link>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: 'var(--bg)', minHeight: '100vh', padding: '40px 0 100px' }}>
      <div className="container">
        
        {/* Top Breadcrumb & Header */}
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
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#79D49B', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
            <ShieldCheck size={16} />
            <span>Stripe 256-Bit SSL Encrypted</span>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '48px',
          alignItems: 'start'
        }}>
          
          {/* Left Column: Contact, Shipping Address & Stripe Payment Element */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            
            {/* 1. Contact Info Section */}
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

            {/* 2. Shipping Address Section */}
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

            {/* 3. Stripe Payment Element Section */}
            <div style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--taupe-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '24px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.15rem', color: 'var(--ink)' }}>
                  3. Payment Details
                </h3>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--brass)' }}>
                  Powered by Stripe
                </span>
              </div>

              {loadingIntent ? (
                <div style={{
                  padding: '32px',
                  textAlign: 'center',
                  color: 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem'
                }}>
                  <Disc size={28} color="var(--brass)" style={{ animation: 'spinSlow 1.5s linear infinite', margin: '0 auto 10px' }} />
                  <div>Initializing secure Stripe checkout...</div>
                </div>
              ) : initError ? (
                <div style={{
                  backgroundColor: 'rgba(140, 47, 47, 0.18)',
                  border: '1px solid var(--seal)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px',
                  color: '#F38A8A',
                  fontSize: '0.85rem'
                }}>
                  {initError}
                </div>
              ) : isZeroTotal ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{
                    backgroundColor: 'rgba(200, 155, 60, 0.15)',
                    border: '1px solid var(--brass)',
                    borderRadius: 'var(--radius-md)',
                    padding: '14px',
                    color: 'var(--ink)',
                    fontSize: '0.88rem'
                  }}>
                    🎉 100% Promotional Discount Applied! Your total amount is <strong>$0.00</strong>. No card payment required.
                  </div>
                  <button
                    onClick={handleZeroTotalCheckout}
                    className="btn-brass"
                    style={{ width: '100%', padding: '16px', fontSize: '1.05rem' }}
                  >
                    <Lock size={18} />
                    <span>Complete Free Order</span>
                  </button>
                </div>
              ) : (clientSecret && !isMockMode) ? (
                <Elements stripe={stripePromise} options={{ clientSecret, appearance: stripeAppearance }}>
                  <StripeCheckoutForm
                    totalAmount={summary?.total || 0}
                    currency={summary?.currency || 'USD'}
                    checkoutId={checkoutId}
                    customerData={formData}
                    isMockMode={false}
                    paymentIntentId={paymentIntentId}
                  />
                </Elements>
              ) : (
                <StripeCheckoutForm
                  totalAmount={summary?.total || 0}
                  currency={summary?.currency || 'USD'}
                  checkoutId={checkoutId}
                  customerData={formData}
                  isMockMode={true}
                  paymentIntentId={paymentIntentId}
                />
              )}
            </div>

          </div>

          {/* Right Column: Authoritative Order Summary Panel */}
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
                <span>${(summary?.subtotal || 0).toFixed(2)}</span>
              </div>
              {summary?.discount > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--brass)' }}>
                  <span>Promotional Discount ({coupon?.code})</span>
                  <span>-${(summary?.discount || 0).toFixed(2)}</span>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink-secondary)' }}>
                <span>Rigid Mailer Courier</span>
                <span>{(summary?.shipping || 0) === 0 ? 'FREE' : `$${(summary?.shipping || 0).toFixed(2)}`}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink)', fontSize: '1.2rem', fontWeight: 600, borderTop: '1px solid var(--taupe-border)', paddingTop: '12px' }}>
                <span>Total Amount</span>
                <span>${(summary?.total || 0).toFixed(2)}</span>
              </div>
            </div>

            <div style={{
              textAlign: 'center',
              marginTop: '20px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-muted)'
            }}>
              🔒 Verified by Stripe 3D Secure
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
