import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStripe, useElements, PaymentElement } from '@stripe/react-stripe-js';
import { Lock, AlertCircle, CheckCircle2, Disc } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { CheckoutService } from '../api/services';
import confetti from 'canvas-confetti';

export default function StripeCheckoutForm({
  totalAmount,
  currency = 'USD',
  checkoutId,
  customerData,
  isMockMode = false,
  paymentIntentId,
  onPaymentSuccess
}) {
  const stripe = useStripe();
  const elements = useElements();
  const navigate = useNavigate();
  const { clearCart, cart } = useCart();

  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [paymentSucceeded, setPaymentSucceeded] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (isProcessing || paymentSucceeded) return;

    setIsProcessing(true);
    setErrorMessage(null);

    // Dev mock mode fallback
    if (isMockMode || !stripe || !elements) {
      try {
        const res = await CheckoutService.completeCheckout({
          payment_intent_id: paymentIntentId || `pi_mock_${checkoutId}`,
        });

        setPaymentSucceeded(true);
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
            order: res,
            items: cart?.items || [],
            total: totalAmount
          }
        });
      } catch (err) {
        setErrorMessage(err.message || 'Payment failed. Please try again.');
        setIsProcessing(false);
      }
      return;
    }

    try {
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/order-success`,
          payment_method_data: {
            billing_details: {
              name: customerData.full_name || 'Collector',
              email: customerData.email || 'guest@otoichi.com',
              address: {
                line1: customerData.street || '',
                city: customerData.city || '',
                state: customerData.state || '',
                postal_code: customerData.postal_code || '',
                country: 'US'
              }
            }
          }
        },
        redirect: 'if_required'
      });

      if (error) {
        if (error.type === 'card_error' || error.type === 'validation_error') {
          setErrorMessage(error.message);
        } else {
          setErrorMessage('An unexpected error occurred processing your payment.');
        }
        setIsProcessing(false);
        return;
      }

      if (paymentIntent && (paymentIntent.status === 'succeeded' || paymentIntent.status === 'processing')) {
        setPaymentSucceeded(true);
        
        // Notify backend of completion
        const completedOrder = await CheckoutService.completeCheckout({
          payment_intent_id: paymentIntent.id,
        }).catch(() => null);

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
            order: completedOrder || { id: checkoutId, status: 'paid', payment_status: paymentIntent.status },
            items: cart?.items || [],
            total: totalAmount
          }
        });
      }
    } catch (err) {
      console.error('Stripe payment confirmation error:', err);
      setErrorMessage(err.message || 'Payment confirmation failed. Please check your card.');
    } finally {
      setIsProcessing(false);
    }
  };

  const getButtonContent = () => {
    if (paymentSucceeded) {
      return (
        <>
          <CheckCircle2 size={18} color="#79D49B" />
          <span>Payment Successful</span>
        </>
      );
    }
    if (isProcessing) {
      return (
        <>
          <Disc size={18} color="var(--ink)" style={{ animation: 'spinSlow 1.5s linear infinite' }} />
          <span>Processing Payment...</span>
        </>
      );
    }
    if (errorMessage) {
      return (
        <>
          <AlertCircle size={18} />
          <span>Try Again</span>
        </>
      );
    }
    return (
      <>
        <Lock size={18} />
        <span>Pay ${Number(totalAmount).toFixed(2)}</span>
      </>
    );
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Stripe Payment Element */}
      {!isMockMode ? (
        <div style={{
          backgroundColor: 'var(--taupe)',
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--taupe-border)'
        }}>
          <PaymentElement
            id="payment-element"
            options={{
              layout: 'tabs',
            }}
          />
        </div>
      ) : (
        <div style={{
          backgroundColor: 'var(--taupe)',
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          border: '1px dashed var(--brass)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.82rem',
          color: 'var(--ink-secondary)'
        }}>
          <div style={{ color: 'var(--brass)', fontWeight: 600, marginBottom: '6px' }}>
            ⚡ Local Dev Test Mode Enabled
          </div>
          <div>Stripe Mock Intent: <span style={{ color: 'var(--ink)' }}>{paymentIntentId}</span></div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '4px' }}>
            Click button below to simulate immediate test payment authorization.
          </div>
        </div>
      )}

      {errorMessage && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: 'rgba(140, 47, 47, 0.18)',
          border: '1px solid var(--seal)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
          color: '#F38A8A',
          fontSize: '0.85rem'
        }}>
          <AlertCircle size={16} style={{ flexShrink: 0 }} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Dynamic CTA Button */}
      <button
        type="submit"
        disabled={isProcessing || paymentSucceeded}
        className="btn-brass"
        style={{
          width: '100%',
          padding: '16px',
          fontSize: '1.05rem',
          opacity: isProcessing ? 0.75 : 1,
          cursor: isProcessing ? 'wait' : 'pointer'
        }}
      >
        {getButtonContent()}
      </button>
    </form>
  );
}
