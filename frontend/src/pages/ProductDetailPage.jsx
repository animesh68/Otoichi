import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Play, Pause, ShoppingBag, ArrowRight, Heart, Zap, ExternalLink, Disc, HelpCircle } from 'lucide-react';
import { CatalogService } from '../api/services';
import { useCart } from '../context/CartContext';
import { useAudio } from '../context/AudioContext';
import StickyBottomBar from '../components/StickyBottomBar';
import ProductCard from '../components/ProductCard';
import VinylDisc from '../components/VinylDisc';
import { getProductDisplay } from '../utils/productHelper';

export default function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { playTrack, currentTrack, isPlaying } = useAudio();

  const [rawProduct, setRawProduct] = useState(null);
  const [albumData, setAlbumData] = useState(null);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [selectedImageTab, setSelectedImageTab] = useState('front');
  const [activeTab, setActiveTab] = useState('description');
  const [showGradingModal, setShowGradingModal] = useState(false);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [showStickyBar, setShowStickyBar] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProductDetails() {
      try {
        setLoading(true);
        let prod = null;
        let alb = null;

        // Try getting album first if id belongs to an album
        try {
          alb = await CatalogService.getAlbumById(id);
        } catch (e) {
          // not directly an album id
        }

        // Try getting product
        try {
          prod = await CatalogService.getProductById(id);
        } catch (e) {
          // not directly a product id
        }

        if (alb) {
          const albProduct = (alb.products && alb.products[0]) ? {
            ...alb.products[0],
            album: alb,
            title: alb.title,
            artist_name: alb.artist_name || alb.artist?.name,
            cover_art_url: alb.cover_art_url
          } : null;

          if (!prod) {
            prod = albProduct || {
              id: alb.id,
              title: alb.title,
              artist_name: alb.artist_name || alb.artist?.name,
              album: alb,
              price: 31.99,
              stock_quantity: 20,
              format: '12" LP',
              sleeve_condition: 'NM',
              media_condition: 'M',
              sku: `OT-LP-${alb.id.substring(0, 8).toUpperCase()}`
            };
          }
        } else if (prod) {
          if (prod.album_id) {
            alb = await CatalogService.getAlbumById(prod.album_id).catch(() => null);
          } else if (prod.album) {
            alb = prod.album;
          }
        }

        if (prod || alb) {
          setRawProduct(prod || alb);
          setAlbumData(alb || prod?.album);

          const genreToSearch = alb?.genre || prod?.genre || 'Rock';
          const simRes = await CatalogService.getProducts({
            genre: genreToSearch,
            limit: 6
          }).catch(() => ({ items: [] }));
          
          const currentId = prod?.id || alb?.id;
          const sims = (simRes?.items || simRes || []).filter(p => p.id !== currentId);
          setSimilarProducts(sims.slice(0, 4));
        }
      } catch (err) {
        console.error('Failed to load product detail:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchProductDetails();
    window.scrollTo(0, 0);
  }, [id]);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 420) {
        setShowStickyBar(true);
      } else {
        setShowStickyBar(false);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const d = getProductDisplay(rawProduct || albumData);

  const handleBuyNow = async () => {
    if (rawProduct) {
      await addToCart(rawProduct, 1);
      navigate('/checkout');
    }
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '80vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg)'
      }}>
        <Disc size={40} color="var(--brass)" style={{ animation: 'spinSlow 2s linear infinite', marginBottom: '16px' }} />
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Retrieving master pressings...
        </p>
      </div>
    );
  }

  if (!rawProduct && !albumData) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '120px 24px', minHeight: '60vh' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: 'var(--ink)', marginBottom: '16px' }}>
          Record Not Found
        </h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
          The requested vinyl pressing is unavailable or no longer listed.
        </p>
        <Link to="/browse" className="btn-brass">
          Browse Record Crates
        </Link>
      </div>
    );
  }

  const rawTracks = (d.tracks && d.tracks.length > 0)
    ? d.tracks
    : (albumData?.tracks && albumData.tracks.length > 0)
      ? albumData.tracks
      : (rawProduct?.track ? [rawProduct.track] : []);

  const isSingle = (rawProduct?.product_type === 'single' || d.format?.includes('7"')) || rawTracks.length === 1;

  let sideATracks = [];
  let sideBTracks = [];

  if (isSingle && rawTracks.length === 1) {
    const singleTrk = rawTracks[0];
    sideATracks = [{ ...singleTrk, title: singleTrk.title, sideLabel: 'A1' }];
    sideBTracks = [{
      ...singleTrk,
      id: `${singleTrk.id || 'single'}_b`,
      title: `${singleTrk.title} (Instrumental / Acoustic B-Side)`,
      sideLabel: 'B1'
    }];
  } else {
    const midPoint = Math.ceil(rawTracks.length / 2);
    sideATracks = rawTracks.slice(0, midPoint);
    sideBTracks = rawTracks.slice(midPoint);
  }

  const formatDuration = (ms) => {
    if (!ms) return '3:45';
    const totalSecs = Math.floor(ms / 1000);
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div style={{ backgroundColor: 'var(--bg)', minHeight: '100vh', padding: '40px 0 120px' }}>
      <div className="container">
        
        {/* Breadcrumb */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
          marginBottom: '32px'
        }}>
          <Link to="/" style={{ color: 'var(--ink-secondary)' }}>Home</Link>
          <span>/</span>
          <Link to="/browse" style={{ color: 'var(--ink-secondary)' }}>Shop</Link>
          <span>/</span>
          <span style={{ color: 'var(--brass)' }}>{d.title}</span>
        </div>

        {/* Top Split Layout: Cover Gallery (Left) & Metadata / Actions (Right) */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '56px',
          marginBottom: '64px'
        }}>
          
          {/* Left Column: Image Viewer + Thumbnails */}
          <div>
            {/* Main Stage */}
            <div style={{
              position: 'relative',
              width: '100%',
              paddingTop: '100%',
              backgroundColor: '#0D0B0A',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--taupe-border)',
              overflow: 'hidden',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {selectedImageTab === 'disc' ? (
                <div style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)'
                }}>
                  <VinylDisc size={280} isSpinning={isPlaying} />
                </div>
              ) : (
                <img
                  src={d.coverArt}
                  alt={d.title}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover'
                  }}
                />
              )}
            </div>

            {/* Thumbnail Strip */}
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
              {[
                { id: 'front', label: 'Front Jacket', img: d.coverArt },
                { id: 'back', label: 'Back Sleeve', img: d.coverArt },
                { id: 'disc', label: 'Vinyl Disc', isDisc: true }
              ].map((thumb) => {
                const isActive = selectedImageTab === thumb.id;
                return (
                  <button
                    key={thumb.id}
                    onClick={() => setSelectedImageTab(thumb.id)}
                    style={{
                      width: '64px',
                      height: '64px',
                      borderRadius: 'var(--radius-md)',
                      border: isActive ? '2px solid var(--brass)' : '1px solid var(--taupe-border)',
                      backgroundColor: 'var(--taupe-dark)',
                      overflow: 'hidden',
                      padding: 0,
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'var(--transition-smooth)'
                    }}
                  >
                    {thumb.isDisc ? (
                      <VinylDisc size={48} />
                    ) : (
                      <img src={thumb.img} alt={thumb.label} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Column: Title, Grading, Price & Actions */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            
            {/* Artist Eyebrow */}
            <div style={{
              color: 'var(--brass)',
              fontFamily: 'var(--font-body)',
              fontSize: '0.9rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '6px'
            }}>
              {d.artistName}
            </div>

            {/* Title in Fraunces Italic Large */}
            <h1 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(2rem, 3.8vw, 3rem)',
              fontStyle: 'italic',
              fontWeight: 400,
              color: 'var(--ink)',
              lineHeight: 1.15,
              marginBottom: '12px'
            }}>
              {d.title}
            </h1>

            {/* Catalog SKU code in IBM Plex Mono */}
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.78rem',
              color: 'var(--text-muted)',
              marginBottom: '20px'
            }}>
              CATALOG NO: <span style={{ color: 'var(--ink-secondary)' }}>{d.sku}</span>
            </div>

            {/* Goldmine Condition Badges + Info Tooltip */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '24px',
              paddingBottom: '20px',
              borderBottom: '1px solid var(--taupe-border)'
            }}>
              <span className="badge-goldmine" style={{ fontSize: '0.8rem', padding: '4px 10px' }}>
                Sleeve: {d.sleeveCondition}
              </span>
              <span className="badge-goldmine badge-media" style={{ fontSize: '0.8rem', padding: '4px 10px' }}>
                Media: {d.mediaCondition}
              </span>
              
              <button
                onClick={() => setShowGradingModal(true)}
                title="What do these grades mean?"
                style={{
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)'
                }}
              >
                <HelpCircle size={14} color="var(--brass)" />
                <span style={{ textDecoration: 'underline' }}>Goldmine Guide</span>
              </button>
            </div>

            {/* Price & Stock Indicator */}
            <div style={{
              display: 'flex',
              alignItems: 'baseline',
              gap: '16px',
              marginBottom: '16px'
            }}>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '2.2rem',
                fontWeight: 600,
                color: 'var(--ink)'
              }}>
                ${d.price.toFixed(2)}
              </div>

              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.82rem',
                color: '#79D49B'
              }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#79D49B' }} />
                <span>IN STOCK</span>
              </div>
            </div>

            {/* Ready to Ship Badge */}
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(46, 125, 78, 0.15)',
              border: '1px solid rgba(121, 212, 155, 0.25)',
              borderRadius: 'var(--radius-md)',
              padding: '6px 12px',
              color: '#79D49B',
              fontSize: '0.82rem',
              fontFamily: 'var(--font-body)',
              width: 'fit-content',
              marginBottom: '28px'
            }}>
              <Zap size={14} />
              <span>Ready to ship — dispatched in custom rigid mailers within 24h</span>
            </div>

            {/* Primary Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '32px' }}>
              <button
                onClick={() => addToCart(rawProduct || albumData, 1)}
                className="btn-brass"
                style={{ flex: 1, padding: '14px 28px', fontSize: '1rem' }}
              >
                <ShoppingBag size={18} />
                <span>Add to Cart</span>
              </button>

              <button
                onClick={handleBuyNow}
                className="btn-outline"
                style={{ flex: 1, padding: '14px 28px', fontSize: '1rem' }}
              >
                <span>Buy Now</span>
                <ArrowRight size={18} />
              </button>

              <button
                onClick={() => setIsWishlisted(!isWishlisted)}
                aria-label="Wishlist record"
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--taupe)',
                  border: isWishlisted ? '1px solid var(--seal)' : '1px solid var(--taupe-border)',
                  color: isWishlisted ? 'var(--seal)' : 'var(--ink)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'var(--transition-smooth)'
                }}
              >
                <Heart size={20} fill={isWishlisted ? 'var(--seal)' : 'none'} />
              </button>
            </div>

            {/* Tab Controls: Description / Attributes */}
            <div style={{
              display: 'flex',
              gap: '24px',
              borderBottom: '1px solid var(--taupe-border)',
              marginBottom: '20px'
            }}>
              <button
                onClick={() => setActiveTab('description')}
                style={{
                  paddingBottom: '12px',
                  fontFamily: 'var(--font-display)',
                  fontSize: '1.15rem',
                  fontStyle: 'italic',
                  color: activeTab === 'description' ? 'var(--brass)' : 'var(--text-muted)',
                  borderBottom: activeTab === 'description' ? '2px solid var(--brass)' : '2px solid transparent'
                }}
              >
                Description
              </button>
              <button
                onClick={() => setActiveTab('attributes')}
                style={{
                  paddingBottom: '12px',
                  fontFamily: 'var(--font-display)',
                  fontSize: '1.15rem',
                  fontStyle: 'italic',
                  color: activeTab === 'attributes' ? 'var(--brass)' : 'var(--text-muted)',
                  borderBottom: activeTab === 'attributes' ? '2px solid var(--brass)' : '2px solid transparent'
                }}
              >
                Attributes
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === 'description' ? (
              <p style={{ color: 'var(--ink-secondary)', lineHeight: '1.7', fontSize: '0.95rem' }}>
                {albumData?.description || (
                  `Original audiophile pressing of ${d.title} by ${d.artistName}. Cut directly from original master analog tapes with immaculate dynamic headroom. Clean labels, original inner sleeve, and play-tested for surface silence.`
                )}
              </p>
            ) : (
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.82rem'
              }}>
                <div style={{ color: 'var(--text-muted)' }}>Format: <span style={{ color: 'var(--ink)' }}>{d.format}</span></div>
                <div style={{ color: 'var(--text-muted)' }}>Speed: <span style={{ color: 'var(--ink)' }}>33 ⅓ RPM</span></div>
                <div style={{ color: 'var(--text-muted)' }}>Weight: <span style={{ color: 'var(--ink)' }}>180g Virgin Vinyl</span></div>
                <div style={{ color: 'var(--text-muted)' }}>Release: <span style={{ color: 'var(--ink)' }}>{d.releaseYear}</span></div>
                <div style={{ color: 'var(--text-muted)' }}>Genre: <span style={{ color: 'var(--ink)' }}>{d.genre}</span></div>
                <div style={{ color: 'var(--text-muted)' }}>Packaging: <span style={{ color: 'var(--ink)' }}>Gatefold Tip-on</span></div>
              </div>
            )}
          </div>
        </div>

        {/* Section 7 Feature: Tracklist formatted by Vinyl Sides (Side A & Side B) */}
        {rawTracks.length > 0 && (
          <section style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--taupe-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '36px',
            marginBottom: '64px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'baseline',
              justifyContent: 'space-between',
              marginBottom: '28px',
              borderBottom: '1px solid rgba(243, 236, 221, 0.08)',
              paddingBottom: '14px'
            }}>
              <div>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.6rem', color: 'var(--ink)', fontWeight: 400 }}>
                  {isSingle ? 'Single Pressing Master Cuts' : 'Master Tracklist'}
                </h3>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--brass)' }}>
                  {isSingle ? '7" 45 RPM VINYL PRESSING SIDES' : 'ORIGINAL VINYL PRESSING SIDES'}
                </span>
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {isSingle ? '2 SIDES TOTAL' : `${rawTracks.length} TRACKS TOTAL`}
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '40px'
            }}>
              {/* SIDE A */}
              <div>
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--brass)',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <Disc size={16} /> SIDE A
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {sideATracks.map((trk, i) => {
                    const isCurrentPlaying = isPlaying && currentTrack?.id === trk.id;
                    const sideLabel = trk.sideLabel || `A${i + 1}`;
                    return (
                      <div
                        key={trk.id || i}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '10px 14px',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: isCurrentPlaying ? 'rgba(200, 155, 60, 0.15)' : 'rgba(243, 236, 221, 0.03)',
                          border: isCurrentPlaying ? '1px solid var(--brass)' : '1px solid transparent',
                          transition: 'var(--transition-smooth)'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                          <button
                            onClick={() => playTrack(trk, albumData || d)}
                            aria-label={`Play ${trk.title}`}
                            style={{
                              width: '30px',
                              height: '30px',
                              borderRadius: '50%',
                              backgroundColor: isCurrentPlaying ? 'var(--brass)' : 'var(--taupe)',
                              color: isCurrentPlaying ? '#100E0C' : 'var(--ink)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            {isCurrentPlaying ? <Pause size={13} fill="#100E0C" /> : <Play size={13} fill="currentColor" style={{ marginLeft: '2px' }} />}
                          </button>

                          <div style={{ minWidth: 0 }}>
                            <div style={{
                              fontFamily: 'var(--font-body)',
                              fontSize: '0.88rem',
                              color: isCurrentPlaying ? 'var(--brass)' : 'var(--ink)',
                              fontWeight: 500,
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }}>
                              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--brass)', marginRight: '8px' }}>{sideLabel}</span>
                              {trk.title}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            {formatDuration(trk.duration_ms)}
                          </span>
                          {trk.spotify_track_id && (
                            <a
                              href={`https://open.spotify.com/track/${trk.spotify_track_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              title="Listen on Spotify"
                              style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}
                            >
                              <ExternalLink size={13} />
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* SIDE B */}
              <div>
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--brass)',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <Disc size={16} /> SIDE B
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {sideBTracks.map((trk, i) => {
                    const isCurrentPlaying = isPlaying && currentTrack?.id === trk.id;
                    const sideLabel = trk.sideLabel || `B${i + 1}`;
                    return (
                      <div
                        key={trk.id || i}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '10px 14px',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: isCurrentPlaying ? 'rgba(200, 155, 60, 0.15)' : 'rgba(243, 236, 221, 0.03)',
                          border: isCurrentPlaying ? '1px solid var(--brass)' : '1px solid transparent',
                          transition: 'var(--transition-smooth)'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                          <button
                            onClick={() => playTrack(trk, albumData || d)}
                            aria-label={`Play ${trk.title}`}
                            style={{
                              width: '30px',
                              height: '30px',
                              borderRadius: '50%',
                              backgroundColor: isCurrentPlaying ? 'var(--brass)' : 'var(--taupe)',
                              color: isCurrentPlaying ? '#100E0C' : 'var(--ink)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            {isCurrentPlaying ? <Pause size={13} fill="#100E0C" /> : <Play size={13} fill="currentColor" style={{ marginLeft: '2px' }} />}
                          </button>

                          <div style={{ minWidth: 0 }}>
                            <div style={{
                              fontFamily: 'var(--font-body)',
                              fontSize: '0.88rem',
                              color: isCurrentPlaying ? 'var(--brass)' : 'var(--ink)',
                              fontWeight: 500,
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }}>
                              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--brass)', marginRight: '8px' }}>{sideLabel}</span>
                              {trk.title}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            {formatDuration(trk.duration_ms)}
                          </span>
                          {trk.spotify_track_id && (
                            <a
                              href={`https://open.spotify.com/track/${trk.spotify_track_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              title="Listen on Spotify"
                              style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}
                            >
                              <ExternalLink size={13} />
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

            </div>
          </section>
        )}

        {/* Similar Picks Carousel */}
        {similarProducts.length > 0 && (
          <section style={{ marginTop: '64px' }}>
            <h3 style={{
              fontFamily: 'var(--font-display)',
              fontSize: '1.8rem',
              color: 'var(--ink)',
              marginBottom: '24px'
            }}>
              Similar Analog Picks
            </h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
              gap: '24px'
            }}>
              {similarProducts.map((sim) => (
                <ProductCard key={sim.id} product={sim} />
              ))}
            </div>
          </section>
        )}

      </div>

      {/* Sticky Bottom Bar (appears on scroll) */}
      <StickyBottomBar product={rawProduct || albumData} visible={showStickyBar} />

      {/* Goldmine Grading Modal */}
      {showGradingModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(0,0,0,0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#1C1814',
            border: '1px solid var(--brass)',
            borderRadius: 'var(--radius-lg)',
            padding: '32px',
            maxWidth: '560px',
            width: '100%',
            boxShadow: '0 20px 50px rgba(0,0,0,0.9)'
          }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.6rem', color: 'var(--ink)', marginBottom: '8px' }}>
              Goldmine Grading Standard
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
              Every Otoichi record is graded under 100W halogen inspection lamps and ultrasonic vacuum cleaned.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontFamily: 'var(--font-body)', fontSize: '0.85rem' }}>
              <div><strong style={{ color: 'var(--brass)' }}>M (Mint):</strong> Absolutely perfect in every way. Never played, possibly sealed.</div>
              <div><strong style={{ color: 'var(--brass)' }}>NM (Near Mint):</strong> A nearly perfect record with no obvious signs of wear.</div>
              <div><strong style={{ color: 'var(--brass)' }}>VG+ (Very Good Plus):</strong> Shows some slight signs of wear, light scuffs with no playback noise.</div>
              <div><strong style={{ color: 'var(--brass)' }}>VG (Very Good):</strong> Surface noise evident in quiet passages, still highly enjoyable.</div>
            </div>
            <button
              onClick={() => setShowGradingModal(false)}
              className="btn-brass"
              style={{ marginTop: '24px', width: '100%' }}
            >
              Understood
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
