import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CartProvider } from './context/CartContext';
import { AudioProvider } from './context/AudioContext';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import AudioPlayerBar from './components/AudioPlayerBar';

// Eagerly import HomePage for fastest First Meaningful Paint
import HomePage from './pages/HomePage';

// Route-level code splitting with lazy loading
const AboutPage = lazy(() => import('./pages/AboutPage'));
const BrowsePage = lazy(() => import('./pages/BrowsePage'));
const ProductDetailPage = lazy(() => import('./pages/ProductDetailPage'));
const CartPage = lazy(() => import('./pages/CartPage'));
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'));
const OrderSuccessPage = lazy(() => import('./pages/OrderSuccessPage'));
const UnsubscribePage = lazy(() => import('./pages/UnsubscribePage'));

function PageSkeleton() {
  return (
    <div style={{
      minHeight: '70vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--bg)',
      color: 'var(--brass)'
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px'
      }}>
        <div style={{
          width: '32px',
          height: '32px',
          border: '2px solid rgba(200, 155, 60, 0.2)',
          borderTopColor: 'var(--brass)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite'
        }} />
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)'
        }}>
          Loading Analog Archive...
        </span>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <CartProvider>
          <AudioProvider>
            <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg)' }}>
              <Navbar />
              <main style={{ flexGrow: 1 }}>
                <Suspense fallback={<PageSkeleton />}>
                  <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/about" element={<AboutPage />} />
                    <Route path="/browse" element={<BrowsePage />} />
                    <Route path="/products/:id" element={<ProductDetailPage />} />
                    <Route path="/albums/:id" element={<ProductDetailPage />} />
                    <Route path="/cart" element={<CartPage />} />
                    <Route path="/checkout" element={<CheckoutPage />} />
                    <Route path="/order-success" element={<OrderSuccessPage />} />
                    <Route path="/newsletter/unsubscribe" element={<UnsubscribePage />} />
                  </Routes>
                </Suspense>
              </main>
              <Footer />
              <AudioPlayerBar />
            </div>
          </AudioProvider>
        </CartProvider>
      </AuthProvider>
    </Router>
  );
}
