import React, { useEffect, useState } from 'react';
import HankoStamp from '../components/HankoStamp';

export default function AboutPage() {
  const [gridTiles, setGridTiles] = useState([]);

  useEffect(() => {
    // Calculate tile grid dynamically based on window size
    const updateGrid = () => {
      const tileSize = 64; // px
      const cols = Math.ceil(window.innerWidth / tileSize);
      const rows = Math.ceil(window.innerHeight / tileSize);
      
      const tiles = [];
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const phase = ((r + c) * 0.12).toFixed(2);
          tiles.push({ id: `${r}-${c}`, row: r, col: c, phase });
        }
      }
      setGridTiles(tiles);
    };

    updateGrid();
    window.addEventListener('resize', updateGrid);
    return () => window.removeEventListener('resize', updateGrid);
  }, []);

  return (
    <div style={{
      position: 'relative',
      minHeight: '100vh',
      width: '100vw',
      overflow: 'hidden',
      backgroundColor: 'var(--bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 24px'
    }}>
      {/* Animated Wave Tile Grid Background */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(64px, 1fr))',
        gridAutoRows: '64px',
        zIndex: 1,
        pointerEvents: 'none',
        opacity: 0.85
      }}>
        {gridTiles.map((tile) => (
          <div
            key={tile.id}
            style={{
              width: '100%',
              height: '100%',
              border: '1px solid rgba(243, 236, 221, 0.02)',
              animation: 'waveCycle 5s ease-in-out infinite',
              animationDelay: `${tile.phase}s`,
              borderRadius: '2px'
            }}
          />
        ))}
      </div>

      {/* Subtle Central Scrim Overlay */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '720px',
        height: '600px',
        background: 'radial-gradient(circle, rgba(16, 14, 12, 0.88) 0%, rgba(16, 14, 12, 0.6) 60%, transparent 90%)',
        filter: 'blur(30px)',
        zIndex: 2,
        pointerEvents: 'none'
      }} />

      {/* About Manifesto Content */}
      <div style={{
        position: 'relative',
        zIndex: 10,
        maxWidth: '680px',
        textAlign: 'center',
        padding: '20px'
      }}>
        {/* Header Title with Brush Script and Seal Stamp */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '14px',
          marginBottom: '32px'
        }}>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(2.4rem, 5vw, 3.4rem)',
            fontWeight: 340,
            color: 'var(--ink)',
            lineHeight: 1.1,
            letterSpacing: '0.02em'
          }}>
            Otoichi <span style={{ fontFamily: 'var(--font-script)', color: 'var(--brass)', fontSize: '0.8em', marginLeft: '4px' }}>音市</span>
          </h1>
          <HankoStamp text="市" size={24} rotation={4} />
        </div>

        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.82rem',
          color: 'var(--brass)',
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          marginBottom: '36px'
        }}>
          A Sound Market • Dedicated to Analog Sound
        </div>

        <div style={{
          fontFamily: 'var(--font-body)',
          fontSize: 'clamp(1.05rem, 2vw, 1.25rem)',
          lineHeight: '1.8',
          color: 'var(--ink-secondary)',
          fontWeight: 400,
          display: 'flex',
          flexDirection: 'column',
          gap: '24px'
        }}>
          <p>
            We deal in <strong style={{ color: 'var(--ink)', fontWeight: 600 }}>pressings, not streams</strong>. Every record here has been listened to before it's listed, sleeve and media graded separately, so the price reflects what's actually in the jacket — no surprises when it arrives.
          </p>

          <p style={{ color: 'var(--text-muted)', fontSize: '0.98em' }}>
            Built for crate-diggers, first-time buyers, and everyone still willing to get up and flip the record.
          </p>
        </div>

        <div style={{
          marginTop: '44px',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 20px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--taupe-border)',
          backgroundColor: 'rgba(243, 236, 221, 0.04)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.78rem',
          color: 'var(--text-muted)'
        }}>
          <span>ANALOG MASTERS</span>
          <span style={{ color: 'var(--brass)' }}>•</span>
          <span>GOLDMINE CERTIFIED</span>
          <span style={{ color: 'var(--brass)' }}>•</span>
          <span>WORLDWIDE CRATE SHIPPING</span>
        </div>
      </div>
    </div>
  );
}
