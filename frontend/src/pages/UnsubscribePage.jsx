import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { CheckCircle2, AlertCircle, Loader2, ArrowLeft, Disc } from 'lucide-react';
import { NewsletterService } from '../api/services';

export default function UnsubscribePage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState('loading'); // 'loading' | 'success' | 'error' | 'no_token'
  const [userEmail, setUserEmail] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('no_token');
      return;
    }

    let isMounted = true;
    const executeUnsubscribe = async () => {
      try {
        setStatus('loading');
        const res = await NewsletterService.unsubscribe(token);
        if (isMounted) {
          setUserEmail(res?.email || '');
          setStatus('success');
        }
      } catch (err) {
        if (isMounted) {
          console.error('Unsubscribe failed:', err);
          setStatus('error');
          setErrorMessage(err?.data?.message || err?.message || 'Invalid or expired unsubscribe link.');
        }
      }
    };

    executeUnsubscribe();
    return () => {
      isMounted = false;
    };
  }, [token]);

  return (
    <div style={{
      minHeight: '80vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 16px',
      backgroundColor: 'var(--bg)'
    }}>
      <div style={{
        maxWidth: '520px',
        width: '100%',
        backgroundColor: '#120F0D',
        border: '1px solid var(--taupe-border)',
        borderRadius: 'var(--radius-md)',
        padding: '48px 36px',
        textAlign: 'center',
        boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'rgba(200, 155, 60, 0.1)',
          color: 'var(--brass)',
          marginBottom: '24px'
        }}>
          <Disc size={28} />
        </div>

        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: '1.75rem',
          color: 'var(--ink)',
          marginBottom: '8px',
          fontWeight: 400
        }}>
          Letters from the Listening Room
        </h1>

        <p style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          color: 'var(--brass)',
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          marginBottom: '32px'
        }}>
          Newsletter Preferences
        </p>

        {status === 'loading' && (
          <div style={{ padding: '32px 0' }}>
            <Loader2 size={36} className="spin-slow" style={{ color: 'var(--brass)', margin: '0 auto 16px' }} />
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Processing your unsubscribe request...
            </p>
          </div>
        )}

        {status === 'success' && (
          <div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              color: '#4ADE80',
              backgroundColor: 'rgba(74, 222, 128, 0.08)',
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '0.85rem',
              marginBottom: '20px'
            }}>
              <CheckCircle2 size={16} />
              <span>Unsubscribed Successfully</span>
            </div>

            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: '0.95rem',
              color: 'var(--text-muted)',
              lineHeight: '1.6',
              marginBottom: '32px'
            }}>
              {userEmail ? <strong>{userEmail}</strong> : 'Your email'} has been removed from our Monday morning dispatch list. You will no longer receive weekly vinyl feature issues.
            </p>

            <Link
              to="/"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 24px',
                backgroundColor: 'var(--brass)',
                color: '#100E0C',
                borderRadius: 'var(--radius-sm)',
                textDecoration: 'none',
                fontFamily: 'var(--font-body)',
                fontWeight: 600,
                fontSize: '0.88rem'
              }}
            >
              <ArrowLeft size={16} /> Return to Storefront
            </Link>
          </div>
        )}

        {(status === 'error' || status === 'no_token') && (
          <div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              color: '#F87171',
              backgroundColor: 'rgba(248, 113, 113, 0.08)',
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '0.85rem',
              marginBottom: '20px'
            }}>
              <AlertCircle size={16} />
              <span>{status === 'no_token' ? 'Missing Authorization Token' : 'Unsubscribe Issue'}</span>
            </div>

            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: '0.95rem',
              color: 'var(--text-muted)',
              lineHeight: '1.6',
              marginBottom: '32px'
            }}>
              {status === 'no_token'
                ? 'No valid unsubscribe token was provided in the URL link. Please use the personalized unsubscribe link located at the bottom of your weekly newsletter email.'
                : errorMessage}
            </p>

            <Link
              to="/"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 24px',
                backgroundColor: 'var(--taupe)',
                color: 'var(--ink)',
                borderRadius: 'var(--radius-sm)',
                textDecoration: 'none',
                fontFamily: 'var(--font-body)',
                fontWeight: 500,
                fontSize: '0.88rem'
              }}
            >
              <ArrowLeft size={16} /> Return to Storefront
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
