import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingBag, Zap } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { getProductDisplay } from '../utils/productHelper';

export default function ProductCard({ product }) {
  const navigate = useNavigate();
  const { addToCart } = useCart();

  const d = getProductDisplay(product);

  const handleCardClick = () => {
    navigate(`/products/${d.id}`);
  };

  const handleAddToCart = (e) => {
    e.stopPropagation();
    addToCart(product, 1);
  };

  return (
    <div
      onClick={handleCardClick}
      style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--taupe-border)',
        overflow: 'hidden',
        cursor: 'pointer',
        transition: 'var(--transition-smooth)',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.borderColor = 'var(--taupe-border-hover)';
        e.currentTarget.style.boxShadow = '0 12px 28px rgba(0,0,0,0.5), 0 0 16px var(--brass-glow)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.borderColor = 'var(--taupe-border)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {/* Cover Art Container */}
      <div style={{
        position: 'relative',
        width: '100%',
        paddingTop: '100%', // 1:1 Aspect Ratio
        backgroundColor: '#0d0c0a',
        overflow: 'hidden'
      }}>
        {d.coverArt ? (
          <img
            src={d.coverArt}
            alt={d.title}
            loading="lazy"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transition: 'transform 0.4s ease'
            }}
          />
        ) : (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'var(--taupe)',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8rem'
          }}>
            NO COVER ART
          </div>
        )}

        {/* Format Badge overlay */}
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          backgroundColor: 'rgba(16, 14, 12, 0.75)',
          backdropFilter: 'blur(6px)',
          border: '1px solid rgba(243, 236, 221, 0.1)',
          borderRadius: 'var(--radius-sm)',
          padding: '3px 8px',
          fontSize: '0.72rem',
          fontFamily: 'var(--font-mono)',
          color: 'var(--ink)'
        }}>
          {d.format}
        </div>
      </div>

      {/* Card Content */}
      <div style={{
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        flexGrow: 1,
        justifyContent: 'space-between'
      }}>
        <div>
          <div style={{
            color: 'var(--brass)',
            fontSize: '0.78rem',
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            marginBottom: '4px',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}>
            {d.artistName}
          </div>

          <h3 style={{
            fontFamily: 'var(--font-display)',
            fontSize: '1.05rem',
            fontWeight: 500,
            color: 'var(--ink)',
            lineHeight: '1.3',
            marginBottom: '10px',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            minHeight: '2.6em'
          }}>
            {d.title}
          </h3>

          {/* Condition & Shipping Badges */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '6px',
            marginBottom: '14px'
          }}>
            <span className="badge-goldmine" title="Sleeve condition (Goldmine grading)">
              S:{d.sleeveCondition}
            </span>
            <span className="badge-goldmine badge-media" title="Media/Vinyl condition (Goldmine grading)">
              M:{d.mediaCondition}
            </span>
            <span className="badge-ready">
              <Zap size={11} /> Ready
            </span>
          </div>
        </div>

        {/* Bottom Row: Price + Circular Add Button */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: 'auto',
          paddingTop: '8px',
          borderTop: '1px solid rgba(243, 236, 221, 0.06)'
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '1.15rem',
            fontWeight: 600,
            color: 'var(--ink)'
          }}>
            ${d.price.toFixed(2)}
          </div>

          {/* Circular Add-to-Cart Button */}
          <button
            onClick={handleAddToCart}
            aria-label="Add to cart"
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '50%',
              backgroundColor: 'var(--taupe)',
              border: '1px solid var(--taupe-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--ink)',
              transition: 'var(--transition-smooth)',
              boxShadow: '0 2px 6px rgba(0,0,0,0.3)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--brass)';
              e.currentTarget.style.color = '#100E0C';
              e.currentTarget.style.borderColor = 'var(--brass)';
              e.currentTarget.style.transform = 'scale(1.08)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--taupe)';
              e.currentTarget.style.color = 'var(--ink)';
              e.currentTarget.style.borderColor = 'var(--taupe-border)';
              e.currentTarget.style.transform = 'scale(1)';
            }}
          >
            <ShoppingBag size={17} />
          </button>
        </div>
      </div>
    </div>
  );
}
