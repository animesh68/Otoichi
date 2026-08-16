import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CartProvider } from './context/CartContext';
import { AudioProvider } from './context/AudioContext';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import AudioPlayerBar from './components/AudioPlayerBar';

import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import BrowsePage from './pages/BrowsePage';
import ProductDetailPage from './pages/ProductDetailPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import OrderSuccessPage from './pages/OrderSuccessPage';

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <CartProvider>
          <AudioProvider>
            <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg)' }}>
              <Navbar />
              <main style={{ flexGrow: 1 }}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/about" element={<AboutPage />} />
                  <Route path="/browse" element={<BrowsePage />} />
                  <Route path="/products/:id" element={<ProductDetailPage />} />
                  <Route path="/albums/:id" element={<ProductDetailPage />} />
                  <Route path="/cart" element={<CartPage />} />
                  <Route path="/checkout" element={<CheckoutPage />} />
                  <Route path="/order-success" element={<OrderSuccessPage />} />
                </Routes>
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
