import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useCart } from '../context/CartContext';

export default function Navbar() {
  const location = useLocation();
  const { itemCount } = useCart();

  const isHeroOverlay = location.pathname === '/' || location.pathname === '/about';

  return (
    <header style={{
      position: isHeroOverlay ? 'absolute' : 'sticky',
      top: 0,
      left: 0,
      width: '100%',
      zIndex: 100,
      backgroundColor: isHeroOverlay ? 'transparent' : 'var(--bg)',
      borderBottom: isHeroOverlay ? '1px solid rgba(243, 236, 221, 0.06)' : '1px solid var(--taupe-border)',
      transition: 'background-color 0.3s ease'
    }}>
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '76px'
      }}>
        {/* Brand Logo: Vinyl Record Glyph in Rounded Square + Otoichi */}
        <Link to="/" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          textDecoration: 'none'
        }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            backgroundColor: 'var(--taupe)',
            border: '1px solid rgba(200, 155, 60, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)'
          }}>
            {/* Minimal Vinyl Disc Glyph */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="9" stroke="var(--ink)" strokeWidth="1.75" />
              <circle cx="12" cy="12" r="6" stroke="rgba(243, 236, 221, 0.35)" strokeWidth="1" />
              <circle cx="12" cy="12" r="3.2" fill="var(--brass)" />
              <circle cx="12" cy="12" r="1.1" fill="var(--bg)" />
            </svg>
          </div>
          <span style={{
            fontFamily: 'var(--font-body)',
            fontWeight: 600,
            fontSize: '1.2rem',
            letterSpacing: '0.04em',
            color: 'var(--ink)'
          }}>
            Otoichi
          </span>
        </Link>

        {/* Exactly Three Nav Items: About, Browse, Cart */}
        <nav style={{
          display: 'flex',
          alignItems: 'center',
          gap: '32px'
        }}>
          <Link to="/about" style={{
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            fontSize: '0.95rem',
            color: location.pathname === '/about' ? 'var(--brass)' : 'var(--ink-secondary)',
            letterSpacing: '0.02em',
            transition: 'var(--transition-smooth)'
          }}>
            About
          </Link>

          <Link to="/browse" style={{
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            fontSize: '0.95rem',
            color: location.pathname === '/browse' ? 'var(--brass)' : 'var(--ink-secondary)',
            letterSpacing: '0.02em',
            transition: 'var(--transition-smooth)'
          }}>
            Browse
          </Link>

          <Link to="/cart" style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            fontSize: '0.95rem',
            color: location.pathname === '/cart' ? 'var(--brass)' : 'var(--ink-secondary)',
            letterSpacing: '0.02em',
            transition: 'var(--transition-smooth)'
          }}>
            <span>Cart</span>
            {itemCount > 0 && (
              <span style={{
                position: 'relative',
                top: '-1px',
                backgroundColor: 'var(--brass)',
                color: '#100E0C',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.72rem',
                fontWeight: 700,
                minWidth: '18px',
                height: '18px',
                borderRadius: 'var(--radius-full)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '0 5px'
              }}>
                {itemCount}
              </span>
            )}
          </Link>
        </nav>
      </div>
    </header>
  );
}
