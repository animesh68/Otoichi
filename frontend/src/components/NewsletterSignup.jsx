import React, { useState } from 'react';
import { Mail, CheckCircle2, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { NewsletterService } from '../api/services';

export default function NewsletterSignup({ variant = 'section' }) {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [status, setStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setStatus('error');
      setErrorMessage('Please enter a valid email address.');
      return;
    }

    try {
      setStatus('loading');
      setErrorMessage('');
      await NewsletterService.subscribe({
        email: email.trim(),
        first_name: firstName.trim() || undefined,
      });
      setStatus('success');
      setEmail('');
      setFirstName('');
    } catch (err) {
      console.error('Newsletter signup error:', err);
      setStatus('error');
      setErrorMessage(err?.data?.message || err?.message || 'Unable to subscribe. Please try again.');
    }
  };

  if (variant === 'compact') {
    return (
      <div style={{ maxWidth: '100%' }}>
        <h4 style={{
          fontFamily: 'var(--font-body)',
          fontSize: '0.85rem',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: 'var(--brass)',
          marginBottom: '8px'
        }}>
          Listening Room Dispatch
        </h4>
        <p style={{
          color: 'var(--text-muted)',
          fontSize: '0.82rem',
          lineHeight: '1.5',
          marginBottom: '14px'
        }}>
          Every Monday, one record worth hearing delivered to your inbox.
        </p>

        {status === 'success' ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 14px',
            backgroundColor: 'rgba(74, 222, 128, 0.08)',
            border: '1px solid rgba(74, 222, 128, 0.25)',
            borderRadius: 'var(--radius-sm)',
            color: '#4ADE80',
            fontSize: '0.82rem'
          }}>
            <CheckCircle2 size={16} />
            <span>Subscribed! Check your inbox on Monday.</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                id="compact-newsletter-email"
                placeholder="your.email@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={status === 'loading'}
                aria-label="Email for weekly newsletter"
                required
                style={{
                  width: '100%',
                  padding: '10px 12px 10px 34px',
                  backgroundColor: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--taupe-border)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--ink)',
                  fontSize: '0.85rem',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
              <Mail size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            </div>

            <button
              type="submit"
              disabled={status === 'loading'}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '9px 14px',
                backgroundColor: 'var(--brass)',
                color: '#100E0C',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-body)',
                fontSize: '0.82rem',
                fontWeight: 600,
                letterSpacing: '0.05em',
                cursor: status === 'loading' ? 'not-allowed' : 'pointer',
                transition: 'var(--transition-smooth)'
              }}
            >
              {status === 'loading' ? <Loader2 size={14} className="spin-slow" /> : 'Subscribe'}
            </button>

            {status === 'error' && (
              <div style={{ color: '#F87171', fontSize: '0.78rem', marginTop: '4px' }}>
                {errorMessage}
              </div>
            )}
          </form>
        )}
      </div>
    );
  }

  // Full Editorial Section Variant
  return (
    <section style={{
      position: 'relative',
      padding: '72px 0',
      backgroundColor: '#0C0A09',
      borderTop: '1px solid var(--taupe-border)',
      borderBottom: '1px solid var(--taupe-border)',
      overflow: 'hidden'
    }}>
      {/* Background Accent Glow */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '500px',
        height: '300px',
        background: 'radial-gradient(circle, rgba(200, 155, 60, 0.08) 0%, rgba(12, 10, 9, 0) 70%)',
        pointerEvents: 'none',
        zIndex: 0
      }} />

      <div className="container" style={{ position: 'relative', zIndex: 1, maxWidth: '720px', textAlign: 'center' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '20px',
          backgroundColor: 'rgba(200, 155, 60, 0.1)',
          border: '1px solid rgba(200, 155, 60, 0.3)',
          color: 'var(--brass)',
          fontSize: '0.78rem',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          marginBottom: '20px'
        }}>
          <Sparkles size={13} />
          <span>Weekly Curated Dispatch</span>
        </div>

        <h2 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(1.8rem, 3.5vw, 2.5rem)',
          fontWeight: 400,
          color: 'var(--ink)',
          marginBottom: '12px',
          letterSpacing: '0.02em'
        }}>
          Letters from the Listening Room
        </h2>

        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: '1.02rem',
          color: 'var(--text-muted)',
          maxWidth: '520px',
          margin: '0 auto 36px',
          lineHeight: '1.6'
        }}>
          Every Monday morning, we feature a singular record from our Tokyo & Kyoto archive worth hearing. Cover artwork, acoustic inspection notes, and 30-second master previews.
        </p>

        {status === 'success' ? (
          <div style={{
            display: 'inline-flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
            padding: '24px 32px',
            backgroundColor: 'rgba(200, 155, 60, 0.06)',
            border: '1px solid var(--brass)',
            borderRadius: 'var(--radius-md)',
            animation: 'fadeIn 0.4s ease-out'
          }}>
            <CheckCircle2 size={32} color="var(--brass)" />
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', color: 'var(--ink)' }}>
              Welcome to the Listening Room
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: 0 }}>
              Your subscription is confirmed. You will receive our next curated pressing on Monday morning.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            maxWidth: '540px',
            margin: '0 auto'
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1.6fr auto',
              gap: '10px',
              alignItems: 'center'
            }}>
              <input
                type="text"
                id="newsletter-firstname"
                placeholder="First Name (optional)"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                disabled={status === 'loading'}
                aria-label="First name"
                style={{
                  padding: '14px 16px',
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--taupe-border)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--ink)',
                  fontSize: '0.9rem',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />

              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  id="newsletter-email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={status === 'loading'}
                  aria-label="Email address"
                  required
                  style={{
                    width: '100%',
                    padding: '14px 16px 14px 38px',
                    backgroundColor: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--taupe-border)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--ink)',
                    fontSize: '0.9rem',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
                <Mail size={16} style={{
                  position: 'absolute',
                  left: '14px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)'
                }} />
              </div>

              <button
                type="submit"
                disabled={status === 'loading'}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 22px',
                  backgroundColor: 'var(--brass)',
                  color: '#100E0C',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontFamily: 'var(--font-body)',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  letterSpacing: '0.04em',
                  cursor: status === 'loading' ? 'not-allowed' : 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'var(--transition-smooth)'
                }}
              >
                {status === 'loading' ? (
                  <>
                    <Loader2 size={16} className="spin-slow" />
                    <span>Joining...</span>
                  </>
                ) : (
                  <span>Subscribe</span>
                )}
              </button>
            </div>

            {status === 'error' && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                color: '#F87171',
                fontSize: '0.84rem',
                marginTop: '6px'
              }}>
                <AlertCircle size={14} />
                <span>{errorMessage}</span>
              </div>
            )}

            <p style={{
              fontSize: '0.76rem',
              color: 'var(--text-muted)',
              marginTop: '12px',
              letterSpacing: '0.02em'
            }}>
              No marketing noise &bull; Direct weekly record recommendation &bull; One-click unsubscribe anytime
            </p>
          </form>
        )}
      </div>
    </section>
  );
}
