import React from 'react';
import { ShoppingBag, ArrowRight } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { useNavigate } from 'react-router-dom';
import { getProductDisplay } from '../utils/productHelper';

export default function StickyBottomBar({ product, visible }) {
  const { addToCart } = useCart();
  const navigate = useNavigate();

  if (!visible || !product) return null;

  const d = getProductDisplay(product);

  const handleBuyNow = async () => {
    await addToCart(product, 1);
    navigate('/checkout');
  };

  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      width: '100%',
      backgroundColor: '#0E0C0A',
      borderTop: '1px solid var(--taupe-border)',
      padding: '12px 0',
      zIndex: 850,
      boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.7)',
      animation: 'slideUp 0.25s ease-out'
    }}>
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Left: Thumbnail + Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0 }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: 'var(--radius-sm)',
            overflow: 'hidden',
            flexShrink: 0,
            backgroundColor: '#000'
          }}>
            {d.coverArt && (
              <img
                src={d.coverArt}
                alt={d.title}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            )}
          </div>

          <div style={{ minWidth: 0 }}>
            <div style={{
              fontSize: '0.75rem',
              color: 'var(--brass)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em'
            }}>
              {d.artistName}
            </div>
            <div style={{
              fontFamily: 'var(--font-display)',
              fontSize: '0.95rem',
              fontStyle: 'italic',
              color: 'var(--ink)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: '360px'
            }}>
              {d.title}
            </div>
          </div>
        </div>

        {/* Right: Price + Stock + Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '1.2rem',
              fontWeight: 600,
              color: 'var(--ink)'
            }}>
              ${d.price.toFixed(2)}
            </span>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: '#79D49B'
            }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#79D49B' }} />
              IN STOCK
            </span>
          </div>

          <button
            onClick={() => addToCart(product, 1)}
            className="btn-brass"
            style={{ padding: '8px 18px', fontSize: '0.88rem' }}
          >
            <ShoppingBag size={15} />
            <span>Add to Cart</span>
          </button>

          <button
            onClick={handleBuyNow}
            className="btn-outline"
            style={{ padding: '8px 18px', fontSize: '0.88rem' }}
          >
            <span>Buy Now</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
