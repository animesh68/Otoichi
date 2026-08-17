import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, Disc } from 'lucide-react';
import CoverflowHero from '../components/CoverflowHero';
import ProductCard from '../components/ProductCard';
import NewsletterSignup from '../components/NewsletterSignup';
import { CatalogService } from '../api/services';

export default function HomePage() {
  const [heroAlbums, setHeroAlbums] = useState([]);
  const [recentProducts, setRecentProducts] = useState([]);
  const [featuredLPs, setFeaturedLPs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadHomeData() {
      try {
        setLoading(true);
        const [albumsRes, productsRes] = await Promise.all([
          CatalogService.getAlbums({ limit: 16 }),
          CatalogService.getProducts({ limit: 24, sort_by: 'newest' })
        ]);

        const albumList = albumsRes?.items || albumsRes || [];
        const productList = productsRes?.items || productsRes || [];

        // Shuffle / rotate albums lightly for dynamic experience across visits
        const shuffledAlbums = [...albumList].sort(() => 0.5 - Math.random());
        setHeroAlbums(shuffledAlbums.slice(0, 9));
        setRecentProducts(productList.slice(0, 8));
        
        // Filter full LP albums
        const lps = productList.filter(p => p.product_type === 'album' || p.format === 'LP');
        setFeaturedLPs(lps.slice(0, 8));
      } catch (err) {
        console.error('Failed to load home page catalog data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadHomeData();
  }, []);

  return (
    <div style={{ backgroundColor: 'var(--bg)', minHeight: '100vh' }}>
      {/* 3D Perspective Coverflow Hero */}
      <CoverflowHero albums={heroAlbums} />

      {/* Main Content Sections Below Fold */}
      <div className="container" style={{ padding: '60px 24px 100px' }}>
        
        {/* Section 1: Fresh From The Crates */}
        <section style={{ marginBottom: '80px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            marginBottom: '32px',
            borderBottom: '1px solid var(--taupe-border)',
            paddingBottom: '16px'
          }}>
            <div>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.78rem',
                color: 'var(--brass)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                marginBottom: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <Sparkles size={14} /> New Arrivals
              </div>
              <h2 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '2rem',
                color: 'var(--ink)',
                fontWeight: 400
              }}>
                Fresh From The Crates
              </h2>
            </div>

            <Link to="/browse" style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontFamily: 'var(--font-body)',
              fontSize: '0.9rem',
              color: 'var(--brass)',
              fontWeight: 500,
              transition: 'var(--transition-smooth)'
            }}>
              <span>Explore All {recentProducts.length > 0 ? `(${recentProducts.length}+)` : ''}</span>
              <ArrowRight size={16} />
            </Link>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
            gap: '24px'
          }}>
            {recentProducts.map((prod) => (
              <ProductCard key={prod.id} product={prod} />
            ))}
          </div>
        </section>

        {/* Section 2: Featured Full LP Pressings */}
        {featuredLPs.length > 0 && (
          <section style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--taupe-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '40px',
            marginBottom: '80px',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'space-between',
              marginBottom: '32px',
              borderBottom: '1px solid rgba(243, 236, 221, 0.08)',
              paddingBottom: '16px'
            }}>
              <div>
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.78rem',
                  color: 'var(--brass)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  marginBottom: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <Disc size={14} /> Master Analog Pressings
                </div>
                <h2 style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '1.8rem',
                  color: 'var(--ink)',
                  fontWeight: 400
                }}>
                  Featured 12" Vinyl Albums
                </h2>
              </div>

              <Link to="/browse?format=LP" style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                color: 'var(--brass)',
                fontSize: '0.9rem',
                fontWeight: 500
              }}>
                <span>View All 12" LPs</span>
                <ArrowRight size={16} />
              </Link>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
              gap: '24px'
            }}>
              {featuredLPs.map((prod) => (
                <ProductCard key={prod.id} product={prod} />
              ))}
            </div>
          </section>
        )}

        {/* Section 3: Listening Bar Philosophy Banner */}
        <section style={{
          padding: '48px 0',
          borderTop: '1px solid var(--taupe-border)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center'
        }}>
          <p style={{
            fontFamily: 'var(--font-display)',
            fontSize: '1.25rem',
            fontStyle: 'italic',
            color: 'var(--ink)',
            maxWidth: '640px',
            lineHeight: '1.6',
            marginBottom: '24px'
          }}>
            "We deal in pressings, not streams. Every record is inspected, play-tested, and graded under natural light."
          </p>
          <Link to="/about" className="btn-outline">
            Read The Otoichi Manifesto
          </Link>
        </section>

      </div>

      {/* Section 4: Letters from the Listening Room Newsletter */}
      <NewsletterSignup variant="section" />
    </div>
  );
}

