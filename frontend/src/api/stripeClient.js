import { loadStripe } from '@stripe/stripe-js';

// Load Stripe with publishable key or fallback for local development
const publishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 'pk_test_51MockKeyForDevOnly000000000000000000000000000000000000000000000000000000000000000000000000000000';

export const stripePromise = loadStripe(publishableKey);
