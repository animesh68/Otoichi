import React from 'react';
import { X, Check } from 'lucide-react';

const GENRES = ['All', 'Rock', 'Alternative Rock', 'Hip-Hop', 'J-Pop', 'Anime OST', 'Classic Rock', 'Soul / R&B'];
const FORMATS = ['All', '12" LP', '7" Single', '10" EP'];
const CONDITIONS = ['All', 'M (Mint)', 'NM (Near Mint)', 'VG+ (Very Good Plus)', 'VG (Very Good)'];

export default function FilterDrawer({
  isOpen,
  onClose,
  selectedGenre,
  setSelectedGenre,
  selectedFormat,
  setSelectedFormat,
  selectedCondition,
  setSelectedCondition,
  priceRange,
  setPriceRange,
  onReset
}) {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: '100%',
      maxWidth: '380px',
      height: '100vh',
      backgroundColor: '#161310',
      borderLeft: '1px solid var(--taupe-border)',
      boxShadow: '-10px 0 40px rgba(0,0,0,0.8)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      animation: 'slideInRight 0.25s ease-out'
    }}>
      {/* Header */}
      <div style={{
        padding: '24px',
        borderBottom: '1px solid var(--taupe-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', color: 'var(--ink)' }}>
            Filter Catalog
          </h3>
          <span style={{ fontFamily: 'var(--font-script)', color: 'var(--brass)', fontSize: '1rem' }}>絞込</span>
        </div>
        <button
          onClick={onClose}
          aria-label="Close filters"
          style={{ color: 'var(--text-muted)', padding: '6px' }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Body Options */}
      <div style={{
        padding: '24px',
        overflowY: 'auto',
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: '28px'
      }}>
        {/* Genre Section */}
        <div>
          <label style={{
            display: 'block',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.78rem',
            textTransform: 'uppercase',
            color: 'var(--brass)',
            marginBottom: '12px'
          }}>
            Genre
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {GENRES.map((g) => {
              const active = (g === 'All' && !selectedGenre) || selectedGenre === g;
              return (
                <button
                  key={g}
                  onClick={() => setSelectedGenre(g === 'All' ? '' : g)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.82rem',
                    fontFamily: 'var(--font-body)',
                    border: active ? '1px solid var(--brass)' : '1px solid var(--taupe-border)',
                    backgroundColor: active ? 'rgba(200, 155, 60, 0.15)' : 'var(--taupe)',
                    color: active ? 'var(--brass)' : 'var(--ink-secondary)',
                    transition: 'var(--transition-smooth)'
                  }}
                >
                  {g}
                </button>
              );
            })}
          </div>
        </div>

        {/* Format Section */}
        <div>
          <label style={{
            display: 'block',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.78rem',
            textTransform: 'uppercase',
            color: 'var(--brass)',
            marginBottom: '12px'
          }}>
            Vinyl Format
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {FORMATS.map((f) => {
              const active = (f === 'All' && !selectedFormat) || selectedFormat === f;
              return (
                <button
                  key={f}
                  onClick={() => setSelectedFormat(f === 'All' ? '' : f)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.82rem',
                    fontFamily: 'var(--font-body)',
                    border: active ? '1px solid var(--brass)' : '1px solid var(--taupe-border)',
                    backgroundColor: active ? 'rgba(200, 155, 60, 0.15)' : 'var(--taupe)',
                    color: active ? 'var(--brass)' : 'var(--ink-secondary)',
                    transition: 'var(--transition-smooth)'
                  }}
                >
                  {f}
                </button>
              );
            })}
          </div>
        </div>

        {/* Condition Section */}
        <div>
          <label style={{
            display: 'block',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.78rem',
            textTransform: 'uppercase',
            color: 'var(--brass)',
            marginBottom: '12px'
          }}>
            Goldmine Condition
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {CONDITIONS.map((c) => {
              const code = c.split(' ')[0];
              const active = (code === 'All' && !selectedCondition) || selectedCondition === code;
              return (
                <button
                  key={c}
                  onClick={() => setSelectedCondition(code === 'All' ? '' : code)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: active ? 'rgba(200, 155, 60, 0.12)' : 'var(--taupe-dark)',
                    border: active ? '1px solid var(--brass)' : '1px solid var(--taupe-border)',
                    color: active ? 'var(--brass)' : 'var(--ink)',
                    fontSize: '0.85rem'
                  }}
                >
                  <span>{c}</span>
                  {active && <Check size={16} color="var(--brass)" />}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div style={{
        padding: '20px 24px',
        borderTop: '1px solid var(--taupe-border)',
        display: 'flex',
        gap: '12px'
      }}>
        <button
          onClick={onReset}
          className="btn-outline"
          style={{ flex: 1, padding: '10px' }}
        >
          Reset All
        </button>
        <button
          onClick={onClose}
          className="btn-brass"
          style={{ flex: 1, padding: '10px' }}
        >
          Apply Filters
        </button>
      </div>
    </div>
  );
}
