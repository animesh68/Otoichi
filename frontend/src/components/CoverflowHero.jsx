import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VinylDisc from './VinylDisc';
import HankoStamp from './HankoStamp';

export default function CoverflowHero({ albums = [] }) {
  const navigate = useNavigate();
  const containerRef = useRef(null);
  
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [focusedIndex, setFocusedIndex] = useState(null);
  const [defaultActiveIndex, setDefaultActiveIndex] = useState(0);

  const displayAlbums = albums.slice(0, 9);

  useEffect(() => {
    if (displayAlbums.length > 0) {
      // Pick resting center index
      setDefaultActiveIndex(Math.floor(displayAlbums.length / 2));
    }
  }, [displayAlbums.length]);

  const activeIndex = hoveredIndex !== null
    ? hoveredIndex
    : (focusedIndex !== null ? focusedIndex : defaultActiveIndex);

  const handleCardClick = (album) => {
    if (album?.id) {
      navigate(`/albums/${album.id}`);
    }
  };

  // Handle smooth cursor tracking across the 3D row so no card is ever occluded from interaction
  const handleContainerMouseMove = (e) => {
    if (!containerRef.current || displayAlbums.length === 0) return;
    const rect = containerRef.current.getBoundingClientRect();
    const relativeX = e.clientX - rect.left;
    const ratio = relativeX / rect.width;
    const computedIdx = Math.min(
      displayAlbums.length - 1,
      Math.max(0, Math.floor(ratio * displayAlbums.length))
    );
    setHoveredIndex(computedIdx);
  };

  const handleTouchMove = (e) => {
    if (!containerRef.current || displayAlbums.length === 0 || !e.touches[0]) return;
    const rect = containerRef.current.getBoundingClientRect();
    const relativeX = e.touches[0].clientX - rect.left;
    const ratio = relativeX / rect.width;
    const computedIdx = Math.min(
      displayAlbums.length - 1,
      Math.max(0, Math.floor(ratio * displayAlbums.length))
    );
    setHoveredIndex(computedIdx);
  };

  return (
    <section style={{
      position: 'relative',
      minHeight: '88vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingTop: '96px',
      paddingBottom: '36px',
      backgroundColor: 'var(--bg)',
      overflow: 'hidden',
      userSelect: 'none'
    }}>
      {/* Background Soft Radial Spotlight Glow */}
      <div style={{
        position: 'absolute',
        top: '28%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '720px',
        height: '720px',
        background: 'radial-gradient(circle, rgba(200, 155, 60, 0.12) 0%, rgba(58, 52, 44, 0.05) 50%, transparent 75%)',
        filter: 'blur(55px)',
        pointerEvents: 'none',
        zIndex: 1
      }} />

      {/* Top Center: Wordmark with 音市 script & Hanko Seal */}
      <div style={{
        position: 'relative',
        zIndex: 10,
        textAlign: 'center',
        marginTop: '8px',
        marginBottom: '8px'
      }}>
        <div style={{ display: 'inline-block', position: 'relative' }}>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(3.8rem, 8.5vw, 6.8rem)',
            fontWeight: 340,
            letterSpacing: '0.04em',
            color: 'var(--ink)',
            lineHeight: 1,
            margin: 0,
            textShadow: '0 4px 30px rgba(0,0,0,0.8)'
          }}>
            Otoichi
          </h1>

          {/* 音市 Script & Seal Stamp Accent */}
          <div style={{
            position: 'absolute',
            bottom: '-10px',
            right: '-38px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transform: 'rotate(3deg)',
            pointerEvents: 'none'
          }}>
            <span style={{
              fontFamily: 'var(--font-script)',
              fontSize: 'clamp(1.4rem, 2.5vw, 2.1rem)',
              color: 'var(--brass)',
              lineHeight: 1,
              textShadow: '0 0 12px var(--brass-glow-strong)'
            }}>
              音市
            </span>
            <HankoStamp text="市" size={19} rotation={-4} />
          </div>
        </div>

        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: '0.9rem',
          color: 'var(--text-muted)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          marginTop: '14px'
        }}>
          Artisanal Vinyl Record Market • Original Pressings & Honest Grading
        </p>
      </div>

      {/* 3D Perspective Fan Coverflow Interaction Container */}
      <div
        ref={containerRef}
        onMouseMove={handleContainerMouseMove}
        onMouseLeave={() => setHoveredIndex(null)}
        onTouchMove={handleTouchMove}
        onTouchEnd={() => setHoveredIndex(null)}
        style={{
          position: 'relative',
          zIndex: 10,
          width: '100%',
          maxWidth: '1280px',
          height: '340px',
          perspective: '1200px',
          perspectiveOrigin: '50% 50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '10px 0',
          cursor: 'pointer'
        }}
      >
        <div style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          height: '100%',
          transformStyle: 'preserve-3d'
        }}>
          {displayAlbums.map((album, idx) => {
            const isActive = activeIndex === idx;
            const offsetFromActive = idx - activeIndex;

            // Geometry relative to active popped-forward card
            const baseRotateY = isActive ? 0 : (offsetFromActive < 0 ? 32 : -32);
            const baseTranslateZ = isActive ? 120 : (-Math.abs(offsetFromActive) * 48);
            const baseTranslateX = isActive ? (offsetFromActive * 110) : (offsetFromActive * 92);
            const baseTranslateY = isActive ? -24 : (Math.abs(offsetFromActive) * 6);
            const zIndex = isActive ? 100 : (50 - Math.abs(offsetFromActive));
            const scale = isActive ? 1.25 : (1 - Math.min(0.2, Math.abs(offsetFromActive) * 0.04));

            const artistName = album.artist_name || album.artist?.name || 'Various Artists';

            return (
              <div
                key={album.id || idx}
                style={{
                  position: 'absolute',
                  width: '210px',
                  height: '210px',
                  zIndex: zIndex,
                  transform: `translateX(${baseTranslateX}px) translateY(${baseTranslateY}px) translateZ(${baseTranslateZ}px) rotateY(${baseRotateY}deg) scale(${scale})`,
                  transition: 'transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), z-index 0.2s ease',
                  transformStyle: 'preserve-3d',
                  pointerEvents: 'auto'
                }}
              >
                <button
                  onClick={() => handleCardClick(album)}
                  onMouseEnter={() => setHoveredIndex(idx)}
                  onFocus={() => setFocusedIndex(idx)}
                  onBlur={() => setFocusedIndex(null)}
                  aria-label={`Inspect ${album.title} by ${artistName}`}
                  style={{
                    width: '100%',
                    height: '100%',
                    padding: 0,
                    border: 'none',
                    background: 'transparent',
                    cursor: 'pointer',
                    position: 'relative',
                    outline: focusedIndex === idx ? '2px solid var(--brass)' : 'none',
                    outlineOffset: '6px',
                    filter: isActive
                      ? 'drop-shadow(0 20px 40px rgba(0,0,0,0.9)) drop-shadow(0 0 20px var(--brass-glow-strong))'
                      : 'drop-shadow(0 8px 18px rgba(0,0,0,0.65))'
                  }}
                >
                  {/* Sleeve with ambient floating drift */}
                  <div style={{
                    position: 'relative',
                    width: '100%',
                    height: '100%',
                    animation: isActive ? 'none' : 'ambientDrift 4s ease-in-out infinite',
                    animationDelay: `${(idx * 0.35) % 2}s`
                  }}>
                    {/* Signature Peeking Vinyl Disc */}
                    <div style={{
                      position: 'absolute',
                      top: '12px',
                      right: isActive ? '-58px' : '-22px',
                      width: '186px',
                      height: '186px',
                      zIndex: 1,
                      transition: 'right 0.35s cubic-bezier(0.22, 1, 0.36, 1)',
                      pointerEvents: 'none'
                    }}>
                      <VinylDisc size={186} isSpinning={isActive} />
                    </div>

                    {/* Album Jacket Sleeve */}
                    <div style={{
                      position: 'relative',
                      zIndex: 2,
                      width: '100%',
                      height: '100%',
                      borderRadius: '4px',
                      overflow: 'hidden',
                      backgroundColor: '#1C1814',
                      border: isActive ? '1px solid var(--brass)' : '1px solid rgba(243, 236, 221, 0.15)',
                      boxShadow: 'inset 0 0 10px rgba(0,0,0,0.7), 2px 4px 15px rgba(0,0,0,0.5)',
                      transition: 'border-color 0.25s ease'
                    }}>
                      {album.cover_art_url ? (
                        <img
                          src={album.cover_art_url}
                          alt={album.title}
                          style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover'
                          }}
                        />
                      ) : (
                        <div style={{
                          width: '100%',
                          height: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: 'var(--taupe)',
                          color: 'var(--ink)',
                          fontFamily: 'var(--font-display)',
                          padding: '10px',
                          textAlign: 'center',
                          fontSize: '0.85rem'
                        }}>
                          {album.title}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Album Title Hover Caption Badge */}
                  {isActive && (
                    <div style={{
                      position: 'absolute',
                      bottom: '-54px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      backgroundColor: 'rgba(16, 14, 12, 0.95)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid var(--brass)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '6px 14px',
                      whiteSpace: 'nowrap',
                      color: 'var(--ink)',
                      zIndex: 120,
                      boxShadow: '0 10px 28px rgba(0,0,0,0.9), 0 0 16px var(--brass-glow)'
                    }}>
                      <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.92rem', fontStyle: 'italic' }}>
                        {album.title}
                      </div>
                      <div style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: '0.74rem',
                        color: 'var(--brass)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        fontWeight: 500
                      }}>
                        {artistName} • Inspect Pressing →
                      </div>
                    </div>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Filter Pills Anchored Above Fold Bottom Edge */}
      <div style={{
        position: 'relative',
        zIndex: 15,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexWrap: 'wrap',
        gap: '10px',
        marginTop: '16px'
      }}>
        {['All Records', 'Rock & Indie', 'Hip-Hop & R&B', 'Electronic & Soul', 'New Pressings'].map((pill, i) => (
          <button
            key={pill}
            onClick={() => navigate('/browse')}
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '0.82rem',
              fontWeight: 500,
              padding: '7px 18px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: i === 0 ? 'rgba(200, 155, 60, 0.15)' : 'rgba(243, 236, 221, 0.05)',
              border: i === 0 ? '1px solid var(--brass)' : '1px solid var(--taupe-border)',
              color: i === 0 ? 'var(--brass)' : 'var(--ink-secondary)',
              transition: 'var(--transition-smooth)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--brass)';
              e.currentTarget.style.color = 'var(--brass)';
              e.currentTarget.style.backgroundColor = 'rgba(200, 155, 60, 0.18)';
            }}
            onMouseLeave={(e) => {
              if (i !== 0) {
                e.currentTarget.style.borderColor = 'var(--taupe-border)';
                e.currentTarget.style.color = 'var(--ink-secondary)';
                e.currentTarget.style.backgroundColor = 'rgba(243, 236, 221, 0.05)';
              }
            }}
          >
            {pill}
          </button>
        ))}
      </div>
    </section>
  );
}
