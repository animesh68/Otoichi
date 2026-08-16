import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Trash2, Plus, Minus, ArrowRight, Disc, Tag, ArrowLeft } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { CheckoutService } from '../api/services';
import { getProductDisplay } from '../utils/productHelper';

export default function CartPage() {
  const navigate = useNavigate();
  const { cart, updateQuantity, removeFromCart, coupon, setCoupon, loading } = useCart();
  const [couponCodeInput, setCouponCodeInput] = useState('');
  const [couponError, setCouponError] = useState(null);
  const [couponSuccess, setCouponSuccess] = useState(null);
  const [isValidatingCoupon, setIsValidatingCoupon] = useState(false);

  const items = cart?.items || [];
  
  // Safe calculation of subtotal
  const subtotal = items.reduce((sum, item) => {
    const d = getProductDisplay(item);
    return sum + (d.price * (item.quantity || 1));
  }, 0);
  
  // Calculate discount if coupon applied
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

  const handleApplyCoupon = async (e) => {
    e.preventDefault();
    if (!couponCodeInput.trim()) return;

    setIsValidatingCoupon(true);
    setCouponError(null);
    setCouponSuccess(null);

    try {
      const res = await CheckoutService.validateCoupon(couponCodeInput.trim(), subtotal || 50.0);
      if (res && res.valid) {
        setCoupon(res);
        setCouponSuccess(`Coupon applied: ${res.code} (${res.discount_percent ? `${res.discount_percent}% off` : `$${res.discount_amount} off`})`);
      } else {
        setCouponError(res?.message || 'Invalid or expired coupon code');
      }
    } catch (err) {
      setCouponError(err.message || 'Invalid coupon code (try "VINYL10" or "VIP20")');
    } finally {
      setIsValidatingCoupon(false);
    }
  };

  if (items.length === 0 && !loading) {
    return (
      <div style={{
        backgroundColor: 'var(--bg)',
        minHeight: '80vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 24px'
      }}>
        <div style={{
          textAlign: 'center',
          maxWidth: '480px',
          padding: '48px 32px',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--taupe-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 12px 30px rgba(0,0,0,0.5)'
        }}>
          {/* Centered Record Sleeve Icon */}
          <div style={{
            width: '72px',
            height: '72px',
            borderRadius: '50%',
            backgroundColor: 'var(--taupe)',
            border: '1px solid var(--taupe-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
            color: 'var(--brass)'
          }}>
            <Disc size={36} />
          </div>

          <h2 style={{
            fontFamily: 'var(--font-display)',
            fontSize: '1.8rem',
            color: 'var(--ink)',
            marginBottom: '10px'
          }}>
            Your Crate Is Empty
          </h2>

          <p style={{
            color: 'var(--text-muted)',
            fontSize: '0.92rem',
            lineHeight: '1.6',
            marginBottom: '28px'
          }}>
            No records have been pulled from the shelves yet. Explore original master pressings in the market.
          </p>

          <Link to="/browse" className="btn-brass" style={{ padding: '12px 28px' }}>
            <span>Browse The Shop</span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    );
  }

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
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.4rem', color: 'var(--ink)', fontWeight: 400 }}>
              Shopping Crate
            </h1>
            <span style={{ fontFamily: 'var(--font-script)', color: 'var(--brass)', fontSize: '1.6rem' }}>
              買物籠
            </span>
          </div>

          <Link to="/browse" style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            color: 'var(--brass)',
            fontSize: '0.88rem'
          }}>
            <ArrowLeft size={16} />
            <span>Continue Crate Digging</span>
          </Link>
        </div>

        {/* Two-Column Grid: Item List (Left) & Order Summary (Right) */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '48px',
          alignItems: 'start'
        }}>
          
          {/* Left Column: Horizontal Cart Item Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {items.map((item) => {
              const d = getProductDisplay(item);
              const qty = item.quantity || 1;
              return (
                <div
                  key={item.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '20px',
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--taupe-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 20px',
                    transition: 'var(--transition-smooth)'
                  }}
                >
                  {/* Cover Thumbnail */}
                  <div style={{
                    width: '72px',
                    height: '72px',
                    borderRadius: 'var(--radius-sm)',
                    overflow: 'hidden',
                    flexShrink: 0,
                    backgroundColor: '#0D0B0A'
                  }}>
                    {d.coverArt ? (
                      <img
                        src={d.coverArt}
                        alt={d.title}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <div style={{ width: '100%', height: '100%', backgroundColor: 'var(--taupe)' }} />
                    )}
                  </div>

                  {/* Item Details */}
                  <div style={{ flexGrow: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: '0.78rem',
                      color: 'var(--brass)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      marginBottom: '2px'
                    }}>
                      {d.artistName}
                    </div>
                    <h3 style={{
                      fontFamily: 'var(--font-display)',
                      fontSize: '1.05rem',
                      color: 'var(--ink)',
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      marginBottom: '4px'
                    }}>
                      {d.title}
                    </h3>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '0.75rem',
                      color: 'var(--text-muted)',
                      fontFamily: 'var(--font-mono)'
                    }}>
                      <span>{d.format}</span>
                      <span>•</span>
                      <span className="badge-goldmine" style={{ padding: '1px 5px' }}>
                        M:{d.mediaCondition}
                      </span>
                    </div>
                  </div>

                  {/* Price */}
                  <div style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    color: 'var(--ink)',
                    minWidth: '70px',
                    textAlign: 'right'
                  }}>
                    ${(d.price * qty).toFixed(2)}
                  </div>

                  {/* Quantity Stepper */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    backgroundColor: 'var(--taupe)',
                    border: '1px solid var(--taupe-border)',
                    borderRadius: 'var(--radius-full)',
                    padding: '4px 8px'
                  }}>
                    <button
                      onClick={() => updateQuantity(item.id, qty - 1)}
                      aria-label="Decrease quantity"
                      style={{ color: 'var(--ink)', display: 'flex', alignItems: 'center' }}
                    >
                      <Minus size={13} />
                    </button>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.85rem',
                      minWidth: '20px',
                      textAlign: 'center'
                    }}>
                      {qty}
                    </span>
                    <button
                      onClick={() => updateQuantity(item.id, qty + 1)}
                      aria-label="Increase quantity"
                      style={{ color: 'var(--ink)', display: 'flex', alignItems: 'center' }}
                    >
                      <Plus size={13} />
                    </button>
                  </div>

                  {/* Remove Button */}
                  <button
                    onClick={() => removeFromCart(item.id)}
                    aria-label="Remove item"
                    style={{
                      color: 'var(--text-muted)',
                      padding: '6px',
                      transition: 'var(--transition-smooth)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = 'var(--seal)'}
                    onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Right Column: Order Summary Panel */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--taupe-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '32px',
            boxShadow: '0 8px 30px rgba(0,0,0,0.4)',
            position: 'sticky',
            top: '90px'
          }}>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: '1.4rem',
              color: 'var(--ink)',
              marginBottom: '20px',
              borderBottom: '1px solid var(--taupe-border)',
              paddingBottom: '12px'
            }}>
              Order Summary
            </h2>

            {/* Price Calculations */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink-secondary)' }}>
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>

              {discountAmount > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--brass)' }}>
                  <span>Coupon Discount ({coupon?.code})</span>
                  <span>-${discountAmount.toFixed(2)}</span>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink-secondary)' }}>
                <span>Rigid Mailer Courier</span>
                <span>{shipping === 0 ? 'FREE (Over $100)' : `$${shipping.toFixed(2)}`}</span>
              </div>

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                color: 'var(--ink)',
                fontSize: '1.2rem',
                fontWeight: 600,
                borderTop: '1px solid var(--taupe-border)',
                paddingTop: '16px'
              }}>
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>

            {/* Coupon Input Form */}
            <form onSubmit={handleApplyCoupon} style={{ marginBottom: '24px' }}>
              <label style={{
                display: 'block',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                marginBottom: '8px'
              }}>
                Promotional Coupon
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  backgroundColor: 'var(--taupe)',
                  border: '1px solid var(--taupe-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '6px 12px',
                  flexGrow: 1
                }}>
                  <Tag size={14} color="var(--text-muted)" style={{ marginRight: '8px' }} />
                  <input
                    type="text"
                    placeholder="e.g. VINYL10"
                    value={couponCodeInput}
                    onChange={(e) => setCouponCodeInput(e.target.value.toUpperCase())}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--ink)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.85rem',
                      width: '100%',
                      textTransform: 'uppercase'
                    }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={isValidatingCoupon}
                  className="btn-outline"
                  style={{ padding: '8px 16px', fontSize: '0.82rem' }}
                >
                  {isValidatingCoupon ? '...' : 'Apply'}
                </button>
              </div>

              {couponSuccess && (
                <div style={{ color: '#79D49B', fontSize: '0.78rem', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>
                  ✓ {couponSuccess}
                </div>
              )}
              {couponError && (
                <div style={{ color: '#F38A8A', fontSize: '0.78rem', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>
                  ✗ {couponError}
                </div>
              )}
            </form>

            {/* Checkout CTA */}
            <button
              onClick={() => navigate('/checkout')}
              className="btn-brass"
              style={{ width: '100%', padding: '14px', fontSize: '1rem' }}
            >
              <span>Proceed to Checkout</span>
              <ArrowRight size={18} />
            </button>

            <div style={{
              textAlign: 'center',
              marginTop: '16px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-muted)'
            }}>
              🔒 256-Bit Encrypted Audiophile Checkout
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
