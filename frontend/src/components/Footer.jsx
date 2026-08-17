import React from 'react';
import { Link } from 'react-router-dom';
import NewsletterSignup from './NewsletterSignup';

export default function Footer() {
  return (
    <footer style={{
      backgroundColor: '#0A0807',
      borderTop: '1px solid var(--taupe-border)',
      padding: '64px 0 36px',
      marginTop: 'auto'
    }}>
      <div className="container">
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '40px',
          marginBottom: '48px'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', color: 'var(--ink)' }}>Otoichi</span>
              <span style={{ fontFamily: 'var(--font-script)', fontSize: '1.2rem', color: 'var(--brass)' }}>音市</span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', lineHeight: '1.6', maxWidth: '280px' }}>
              An artisanal sound market dealing in original pressings, late-night imports, and curated audio artifacts.
            </p>
          </div>

          <div>
            <h4 style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--brass)', marginBottom: '16px' }}>
              Grading Standard
            </h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: '1.6' }}>
              Every item is inspected according to strict Goldmine Grading standards. Sleeve and media are graded separately.
            </p>
          </div>

          <div>
            <h4 style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--brass)', marginBottom: '16px' }}>
              Navigation
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <Link to="/browse" style={{ color: 'var(--ink-secondary)', fontSize: '0.88rem', transition: 'var(--transition-smooth)' }}>
                Browse All Vinyl
              </Link>
              <Link to="/about" style={{ color: 'var(--ink-secondary)', fontSize: '0.88rem', transition: 'var(--transition-smooth)' }}>
                About Otoichi (音市)
              </Link>
              <Link to="/cart" style={{ color: 'var(--ink-secondary)', fontSize: '0.88rem', transition: 'var(--transition-smooth)' }}>
                View Cart
              </Link>
            </div>
          </div>

          <div>
            <NewsletterSignup variant="compact" />
          </div>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          paddingTop: '24px',
          borderTop: '1px solid rgba(243, 236, 221, 0.06)',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)'
        }}>
          <div>© {new Date().getFullYear()} OTOICHI (音市). ALL RIGHTS RESERVED.</div>
          <div style={{ display: 'flex', gap: '20px' }}>
            <span>PRESSINGS NOT STREAMS</span>
            <span style={{ color: 'var(--brass)' }}>•</span>
            <span>GOLDMINE VERIFIED</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
